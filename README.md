# AptiTalent Educational Video Compressor Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-7.1.1-green.svg)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-efficiency video compression engine optimized for educational screen recordings. Features a modern web interface with profile-driven adaptive encoding (AV1, HEVC, H.264), intelligent quality presets, visual quality benchmarking (SSIM/PSNR), and custom configuration options designed specifically for tutorials, lectures, and presentations.

## ✨ Features

- **Web-Based Interface**: Intuitive drag-and-drop web UI for easy video compression
- **Profile-Driven Adaptive Encoding**: Generates high-efficiency single-file video streams using AV1, HEVC, or H.264 codecs tailored to bandwidth requirements
- **Smart Quality Presets**: Five proportional profiles for educational content:
  - **Quality Optimized**: 1080p @ 30fps (highest visual quality, ~2.5 Mbps video cap)
  - **Balanced**: 720p @ 30fps (recommended sweet-spot, ~1.2 Mbps video cap)
  - **Storage Optimized**: 540p @ 20fps (compact size with readable text, ~450 kbps video cap, ~3.7 MB/min)
  - **Extreme Compression**: 360p @ 15fps (high compression, ~200 kbps video cap, ~1.8 MB/min)
  - **Ultra Extreme**: 240p @ 12fps (maximum storage priority, ~100 kbps video cap, ~0.9 MB/min)
- **Codec Selection**: Choose between AV1, HEVC, or H.264 for encoding
- **Custom Configuration**: Full control over resolution, FPS, CRF, and audio bitrate within supported parameters
- **Screen Recording Optimization**: Uses `-tune stillimage` for maximum text clarity at low bitrates
- **Automated Quality Benchmarking**: Integrated SSIM and PSNR visual quality evaluation harness
- **Automatic FFmpeg Management**: Seamless binary detection and auto-download with encoder capability detection
- **Security Features**: File sanitization and SHA-256 integrity verification
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg 7.1.1 (auto-downloaded if not found)
- 2GB RAM minimum (4GB recommended)
- 500MB disk space for FFmpeg binaries

## 🚀 Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd research_for_screen_recording
   ```

2. **Install Python dependencies** (if using pip)
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

3. **Setup FFmpeg** (optional - auto-installs on first run)
   ```bash
   python main.py setup-ffmpeg
   ```

## 🚀 Usage

### Web Interface (Recommended)

**Windows:**
- Double-click `Compress Video.bat`
- Or run: `python main.py server`

**macOS/Linux:**
```bash
python main.py server
```

The web interface will open at `http://localhost:8765`

### Command Line Interface

#### List Available Profiles
```bash
python main.py list-profiles
```

#### Compress a Video File
```bash
# Using preset profiles
python main.py compress -i path/to/video.mp4 --profile balanced

# Using custom configuration
python main.py compress -i path/to/video.mp4 --profile custom --resolution 1280x720 --fps 30 --crf 23 --audio-bitrate 128k
```

#### Run Benchmark Suite
```bash
python main.py benchmark --dataset-dir ./Sample_Videos --profile all
```

#### Setup FFmpeg
```bash
python main.py setup-ffmpeg
```

## 📁 Project Structure

```
research_for_screen_recording/
├── main.py                              # CLI entry point
├── README.md                            # This file
├── Compress Video.bat                   # Windows launcher
├── Setup FFmpeg.bat                     # FFmpeg installer
│
├── src/
│   └── apti_compress/
│       ├── __init__.py                  # Package initialization
│       ├── cli.py                       # Command-line interface
│       ├── pyproject.toml               # Package configuration
│       │
│       ├── core/                        # Core encoding engine
│       │   ├── __init__.py
│       │   ├── encoder.py               # Profile-driven encoding pipeline
│       │   ├── ffmpeg_manager.py        # FFmpeg management & encoder detection
│       │   └── simple_encoder.py        # Legacy H.264 encoder (deprecated)
│       │
│       ├── profiles/                    # Compression profiles
│       │   ├── __init__.py
│       │   ├── base.py                  # Abstract base class
│       │   └── registry.py              # Profile implementations & bitrate math
│       │
│       ├── server/                      # Web server
│       │   ├── __init__.py
│       │   └── compressor_server.py      # FastAPI application
│       │
│       ├── utils/                       # Utilities
│       │   ├── __init__.py
│       │   ├── security.py              # File sanitization
│       │   └── hash.py                  # SHA-256 hashing
│       │
│       ├── metrics/                     # Quality metrics (SSIM / PSNR)
│       │   └── __init__.py
│       │
│       └── benchmarks/                  # Multi-content benchmark suite
│           └── __init__.py
│
├── public/                              # Web interface assets
│   └── compress.html
│
└── Compressed/                          # Output directory (auto-created)
```

## 🎨 Quality Presets

| Preset | Resolution | FPS | Max Video Bitrate | Total Bitrate Cap | Estimated Size / Min | Target & Readability |
|--------|------------|-----|-------------------|-------------------|----------------------|----------------------|
| **Quality Optimized** | 1080p (`1920x1080`) | 30 | 2,500 kbps | ~2,628 kbps | ~18.8 MB/min | Highest visual fidelity & font detail |
| **Balanced** | 720p (`1280x720`) | 30 | 1,200 kbps | ~1,296 kbps | ~9.3 MB/min | Recommended sweet spot for tutorials |
| **Storage Optimized** | 540p (`960x540`) | 20 | 450 kbps | ~514 kbps | ~3.7 MB/min | Compact size with readable text & code |
| **Extreme Compression** | 360p (`640x360`) | 15 | 200 kbps | ~248 kbps | ~1.8 MB/min | Text-optimized extreme compression |
| **Ultra Extreme** | 240p (`426x240`) | 12 | 100 kbps | ~132 kbps | ~0.9 MB/min | Maximum storage priority with structural clarity |

**Custom Configuration**: Use the web interface or CLI to specify any resolution, FPS, CRF (18-40), and audio bitrate for complete control.

*Note: Estimated MB/min values and bitrate caps (`-maxrate`) represent maximum ceiling budgets. Actual output file sizes vary dynamically based on video content complexity and CRF rate control.*

## 📊 Quality & Compression Benchmarks

The engine includes an automated benchmark harness (`apti_compress.benchmarks`) that measures real SSIM (Structural Similarity) and PSNR (Peak Signal-to-Noise Ratio) against reference videos using FFmpeg filters.

To run dynamic quality benchmarks on your dataset:
```bash
python main.py benchmark --dataset-dir ./Sample_Videos --profile all
```

*Visual quality metrics (SSIM / PSNR), file size reduction percentages, and encoding throughput are calculated dynamically per video run based on actual video content.*

## 🔧 Configuration

### Server Configuration
```bash
python main.py server --host 127.0.0.1 --port 8765
```

### Profile Selection
The web interface allows real-time profile selection. CLI usage:
```bash
python main.py compress -i video.mp4 --profile quality
python main.py compress -i video.mp4 --profile balanced
python main.py compress -i video.mp4 --profile storage
python main.py compress -i video.mp4 --profile extreme
```

## 🛠️ Troubleshooting

### FFmpeg Not Found
- Run `python main.py setup-ffmpeg` to auto-install
- Or manually download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Encoding Fails
- Ensure input video format is supported (MP4, MOV, AVI, MKV, WEBM, FLV, TS)
- Check available disk space in output directory
- Verify FFmpeg installation with `ffmpeg -version`

### Server Won't Start
- Check if port 8765 is already in use
- Try a different port: `python main.py server --port 8080`
- Ensure Python dependencies are installed

## 📊 Technical Details

### Encoding Pipeline
1. **Input Validation**: File format and video duration analysis via FFprobe
2. **Encoder Detection**: Inspects local build for AV1 (`libaom-av1`), HEVC (`libx265`), and H.264 (`libx264`)
3. **Profile Strategy Application**: Applies selected profile strategy (Quality, Balanced, Storage, Extreme, Ultra Extreme, or Custom)
4. **Target Encoding**: Encodes single compressed output file using selected codec and profile parameters
5. **Screen Recording Optimization**: Applies `-tune stillimage` for sharp font and UI text clarity
6. **Filename & Timestamping**: Appends resolution tag and time timestamp (`_360p_h264_204240.mp4`) to prevent file collisions
7. **Threadpool Offloading**: Offloads encoding subprocess to background threadpool so FastAPI event loop remains responsive
8. **Fast Start**: Applies `-movflags +faststart` for web playback compatibility

### Security
- Input filename sanitization to prevent path traversal
- SHA-256 hash verification for downloaded binaries
- Temporary file cleanup after processing

## 📝 API Endpoints

- `GET /` - Web interface
- `GET /api/status` - Server and FFmpeg status
- `GET /api/presets` - Available quality presets
- `POST /api/compress` - Compress uploaded video
- `GET /api/open-folder` - Open output folder in file explorer

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All features include error handling
- Changes maintain backward compatibility

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- FFmpeg team for the excellent multimedia framework
- FastAPI for the modern web framework
- The open-source community for various utilities
