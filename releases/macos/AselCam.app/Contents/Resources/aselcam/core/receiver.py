import socket
import struct
import subprocess
import threading
import time
try:
    import fcntl
    import termios
    HAS_IOCTL = True
except ImportError:
    fcntl = None
    termios = None
    HAS_IOCTL = False
import array
import numpy as np
from typing import Optional, Callable, Tuple
from .audio_sink import AudioSink
from .v4l2_sink import V4L2Sink
from .filters import VideoFilters

MAGIC = b"ASEL"
TYPE_VIDEO_H264 = 0x01
TYPE_VIDEO_H265 = 0x02
TYPE_AUDIO_PCM = 0x03
TYPE_CODEC_CONFIG = 0x04

HEADER_FORMAT = ">4sB B Q I" # magic(4), type(1), flags(1), timestamp(8), length(4)
HEADER_SIZE = 18

class StreamReceiver:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4747,
        audio_sink: Optional[AudioSink] = None,
        v4l2_sink: Optional[V4L2Sink] = None,
        filters: Optional[VideoFilters] = None
    ):
        self.host = host
        self.port = port
        self.audio_sink = audio_sink
        self.v4l2_sink = v4l2_sink
        self.filters = filters or VideoFilters()

        self._socket: Optional[socket.socket] = None
        self._is_running = False
        self._recv_thread: Optional[threading.Thread] = None
        self._ffmpeg_proc: Optional[subprocess.Popen] = None
        self._read_frame_thread: Optional[threading.Thread] = None
        self._decoder_lock = threading.Lock()
        self._header_buf = bytearray(HEADER_SIZE)

        self.current_width = 1920
        self.current_height = 1080
        self.current_codec = "h264"
        self.is_preview_enabled = True
        self.is_camera_paused = False
        self._last_codec_config: Optional[bytes] = None

        # Telemetry
        self.current_fps: float = 0.0
        self.current_bitrate_kbps: float = 0.0
        self.total_frames_received: int = 0
        self._frames_counter = 0
        self._bytes_counter = 0
        self._last_stats_time = time.time()

        # Callbacks
        self.on_frame_ready: Optional[Callable[[np.ndarray], None]] = None
        self.on_stats_updated: Optional[Callable[[float, float], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None

    def start(self, width: int = 1920, height: int = 1080, codec: str = "h264") -> bool:
        self.stop()
        self.current_width = width
        self.current_height = height
        self.current_codec = codec.lower()
        self._last_codec_config = None

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Low latency socket buffer to prevent queue backlog
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 128 * 1024)
            s.settimeout(5.0)
            s.connect((self.host, self.port))
            s.settimeout(1.0) # 1s timeout for reads
            self._socket = s
            self._is_running = True

            # Start ffmpeg decoder pipe
            self._start_decoder(width, height, codec=self.current_codec)

            # Start socket receiver thread
            self._recv_thread = threading.Thread(target=self._receive_loop, name="AselCam-RecvThread", daemon=True)
            self._recv_thread.start()

            print(f"[Receiver] Bağlandı {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[Receiver] Bağlantı kurulamadı: {e}")
            self.stop()
            return False

    def _start_decoder(self, width: int, height: int, codec: str = "h264"):
        with self._decoder_lock:
            self._stop_decoder_unlocked()
            self.current_width = width
            self.current_height = height
            self.current_codec = codec.lower()
            input_format = "hevc" if self.current_codec in ("h265", "hevc") else "h264"
            cmd = [
                "ffmpeg",
                "-v", "warning",
                "-flags", "low_delay",
                "-probesize", "32768",
                "-threads", "1",
                "-f", input_format,
                "-i", "pipe:0",
                "-vf", f"scale={width}:{height}",
                "-f", "rawvideo",
                "-pix_fmt", "rgb24",
                "pipe:1"
            ]
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=0
                )
                self._ffmpeg_proc = proc
                if self._last_codec_config and proc.stdin:
                    try:
                        proc.stdin.write(self._last_codec_config)
                        proc.stdin.flush()
                    except Exception:
                        pass
                self._read_frame_thread = threading.Thread(
                    target=self._decoder_reader_loop,
                    args=(proc, width, height),
                    name="AselCam-DecoderReader",
                    daemon=True
                )
                self._read_frame_thread.start()
            except Exception as e:
                print(f"[Receiver] FFmpeg decoder başlatılamadı: {e}")

    def reconfigure_decoder(self, width: int, height: int, codec: str = "h264"):
        """Safely restarts only the FFmpeg decoder if dimensions or codec changed, without dropping the TCP socket."""
        norm_codec = codec.lower()
        if (self.current_width == width and
            self.current_height == height and
            self.current_codec == norm_codec and
            self._ffmpeg_proc is not None and
            self._ffmpeg_proc.poll() is None
        ):
            return
        self._start_decoder(width, height, norm_codec)

    def _stop_decoder_unlocked(self):
        old_proc = self._ffmpeg_proc
        self._ffmpeg_proc = None
        if old_proc:
            try:
                if old_proc.stdin:
                    old_proc.stdin.close()
            except Exception:
                pass
            try:
                if old_proc.stdout:
                    old_proc.stdout.close()
            except Exception:
                pass
            try:
                old_proc.terminate()
                old_proc.wait(timeout=0.2)
            except Exception:
                try:
                    old_proc.kill()
                except Exception:
                    pass

        if self._read_frame_thread and self._read_frame_thread.is_alive() and threading.current_thread() != self._read_frame_thread:
            self._read_frame_thread.join(timeout=0.3)
        self._read_frame_thread = None

    def _stop_decoder(self):
        with self._decoder_lock:
            self._stop_decoder_unlocked()

    def _recv_exact_into(self, sock: socket.socket, buffer: bytearray, target_len: int) -> bool:
        """Reads exactly target_len bytes into buffer without losing state across socket timeouts."""
        view = memoryview(buffer)
        pos = 0
        while pos < target_len and self._is_running:
            try:
                n = sock.recv_into(view[pos:], target_len - pos)
                if n == 0:
                    return False
                pos += n
            except socket.timeout:
                continue
            except (BlockingIOError, InterruptedError):
                continue
            except Exception:
                return False
        return pos == target_len

    def _read_packet(self, sock: socket.socket) -> Optional[Tuple[int, int, int, bytearray]]:
        """Reads one full ASEL packet with automatic sliding-window resynchronization."""
        if not self._recv_exact_into(sock, self._header_buf, HEADER_SIZE):
            return None

        # Check MAGIC
        if bytes(self._header_buf[:4]) != MAGIC:
            print(f"[Receiver] Senkronizasyon kaybı ({bytes(self._header_buf[:4])}), ASEL aranıyor...")
            scan = bytearray(self._header_buf)
            while self._is_running:
                idx = scan.find(MAGIC)
                if idx != -1:
                    scan = scan[idx:]
                    needed = HEADER_SIZE - len(scan)
                    if needed > 0:
                        more = bytearray(needed)
                        if not self._recv_exact_into(sock, more, needed):
                            return None
                        scan.extend(more)
                    self._header_buf[:HEADER_SIZE] = scan[:HEADER_SIZE]
                    break
                else:
                    scan = scan[-(len(MAGIC) - 1):]
                    b = bytearray(1)
                    if not self._recv_exact_into(sock, b, 1):
                        return None
                    scan.extend(b)

        magic, ptype, flags, ts, payload_len = struct.unpack(HEADER_FORMAT, self._header_buf)
        if magic != MAGIC:
            return None

        if payload_len > 16 * 1024 * 1024 or payload_len < 0:
            print(f"[Receiver] Geçersiz paket boyutu: {payload_len} bayt")
            return None

        payload = bytearray(payload_len)
        if payload_len > 0:
            if not self._recv_exact_into(sock, payload, payload_len):
                return None

        return ptype, flags, ts, payload

    def _receive_loop(self):
        sock = self._socket
        if not sock:
            return

        while self._is_running:
            try:
                packet = self._read_packet(sock)
                if packet is None:
                    if self._is_running:
                        print("[Receiver] Akış sonlandı veya bağlantı kesildi")
                    break

                ptype, flags, ts, payload = packet
                payload_len = len(payload)
                self._bytes_counter += (HEADER_SIZE + payload_len)

                # Dispatch packet by type
                if ptype in (TYPE_VIDEO_H264, TYPE_VIDEO_H265, TYPE_CODEC_CONFIG):
                    if ptype == TYPE_CODEC_CONFIG:
                        self._last_codec_config = bytes(payload)
                    elif ptype == TYPE_VIDEO_H265 and self.current_codec != "hevc":
                        print("[Receiver] H.265 akışı algılandı, çözücü HEVC olarak güncelleniyor...")
                        self._start_decoder(self.current_width, self.current_height, "hevc")
                    elif ptype == TYPE_VIDEO_H264 and self.current_codec == "hevc":
                        print("[Receiver] H.264 akışı algılandı, çözücü H.264 olarak güncelleniyor...")
                        self._start_decoder(self.current_width, self.current_height, "h264")

                    proc = self._ffmpeg_proc
                    if proc is None or proc.poll() is not None:
                        self._start_decoder(self.current_width, self.current_height, self.current_codec)
                        proc = self._ffmpeg_proc

                    if proc and proc.stdin:
                        try:
                            proc.stdin.write(payload)
                            proc.stdin.flush()
                        except (BrokenPipeError, OSError, ValueError, AttributeError):
                            pass

                elif ptype == TYPE_AUDIO_PCM:
                    if self.audio_sink:
                        try:
                            self.audio_sink.write_audio(payload)
                        except Exception:
                            pass

            except Exception as e:
                if self._is_running:
                    print(f"[Receiver] Paket işleme hatası: {e}")
                break

        if self._is_running and self.on_disconnected:
            try:
                self.on_disconnected()
            except Exception:
                pass
        self.stop()

    def _decoder_reader_loop(self, proc: subprocess.Popen, width: int, height: int):
        frame_size = width * height * 3
        frame_buf = bytearray(frame_size)
        view = memoryview(frame_buf)
        stdout = proc.stdout
        if not stdout:
            return

        while self._is_running and self._ffmpeg_proc == proc:
            try:
                pos = 0
                while pos < frame_size and self._is_running and self._ffmpeg_proc == proc:
                    try:
                        nbytes = stdout.readinto(view[pos:])
                        if not nbytes:
                            return
                        pos += nbytes
                    except Exception:
                        return

                if pos != frame_size or self._ffmpeg_proc != proc:
                    break

                self.total_frames_received += 1
                self._frames_counter += 1

                # Update stats every 1 second
                now = time.time()
                elapsed = now - self._last_stats_time
                if elapsed >= 1.0:
                    self.current_fps = round(self._frames_counter / elapsed, 1)
                    self.current_bitrate_kbps = round((self._bytes_counter * 8) / (1024 * elapsed), 1)
                    self._frames_counter = 0
                    self._bytes_counter = 0
                    self._last_stats_time = now
                    if self.on_stats_updated:
                        try:
                            self.on_stats_updated(self.current_fps, self.current_bitrate_kbps)
                        except Exception:
                            pass

                # Convert to numpy RGB image (COPY to ensure thread safety with GUI & v4l2)
                frame_rgb = np.frombuffer(frame_buf, dtype=np.uint8).reshape((height, width, 3)).copy()

                # Discard any stale frames queued in the pipe to keep latency strictly real-time (0ms)
                if HAS_IOCTL and fcntl and termios:
                    try:
                        fionread_buf = array.array('i', [0])
                        fcntl.ioctl(stdout.fileno(), termios.FIONREAD, fionread_buf)
                        queued = fionread_buf[0]
                        if queued >= 2 * frame_size:
                            skip_bytes = ((queued // frame_size) - 1) * frame_size
                            discarded = 0
                            while discarded < skip_bytes and self._is_running:
                                discard_chunk = stdout.read(min(skip_bytes - discarded, 512 * 1024))
                                if not discard_chunk:
                                    break
                                discarded += len(discard_chunk)
                    except Exception:
                        pass

                # Handle Camera Mute/Blackout
                if self.is_camera_paused:
                    frame_rgb = np.zeros_like(frame_rgb)

                # Apply real-time filters
                if self.filters:
                    try:
                        processed = self.filters.apply(frame_rgb)
                    except Exception:
                        processed = frame_rgb
                else:
                    processed = frame_rgb

                # 1. Feed virtual webcam v4l2loopback directly from RGB
                if self.v4l2_sink and self.v4l2_sink.is_open:
                    try:
                        self.v4l2_sink.write_rgb_frame(processed)
                    except Exception:
                        pass

                # 2. Feed GUI preview ONLY if preview is enabled
                if self.is_preview_enabled and self.on_frame_ready:
                    try:
                        if not processed.flags['C_CONTIGUOUS']:
                            processed = np.ascontiguousarray(processed)
                        self.on_frame_ready(processed)
                    except Exception:
                        pass

            except Exception as e:
                if self._is_running and self._ffmpeg_proc == proc:
                    print(f"[Receiver] Kare işleme uyarısı: {e}")

    def set_preview_enabled(self, enabled: bool):
        self.is_preview_enabled = enabled

    def set_camera_paused(self, paused: bool):
        self.is_camera_paused = paused

    def stop(self):
        self._is_running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        self._stop_decoder()

        if self._recv_thread and self._recv_thread.is_alive() and threading.current_thread() != self._recv_thread:
            self._recv_thread.join(timeout=0.5)
        self._recv_thread = None

        if self._read_frame_thread and self._read_frame_thread.is_alive() and threading.current_thread() != self._read_frame_thread:
            self._read_frame_thread.join(timeout=0.5)
        self._read_frame_thread = None
