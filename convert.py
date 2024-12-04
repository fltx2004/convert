import os
import subprocess
import json

# 创建 output 文件夹（如不存在）
output_dir = "output"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

def is_valid_media_file(file_name):
    """
    使用 ffprobe 检查文件是否为支持的媒体文件。
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "format=filename", "-of", "json", file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0 or "error" in result.stderr.lower():
            return False
        return True
    except Exception as e:
        print(f"检查媒体文件有效性时出错：{e}")
        return False


def get_audio_format(video_file):
    """
    使用 ffprobe 获取视频文件中的音频流格式。
    """
    try:
        # ffprobe 命令提取音频流的 codec_name
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "json", video_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        probe_data = json.loads(result.stdout)
        return probe_data["streams"][0]["codec_name"] if "streams" in probe_data and probe_data["streams"] else None
    except json.JSONDecodeError:
        print(f"无法分析文件 '{video_file}' 的格式，可能不是有效的音频/视频文件。")
        return None
    except IndexError:
        print(f"文件 '{video_file}' 中没有音频流！")
        return None
    except Exception as e:
        print(f"解析文件 '{video_file}' 音频格式时出错：{e}")
        return None


def repair_file(input_file, repaired_file):
    """
    使用 FFmpeg 修复或重封装文件。
    """
    try:
        print(f"尝试修复文件: {input_file} -> {repaired_file}")
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,  # 输入文件
                "-c", "copy",  # 不重新编码，而是重封装
                "-f", "mp4",  # 可以写入标准化的 MP4 格式
                repaired_file
            ],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"修复文件失败 '{input_file}'，错误信息：{e}")
        return False


def convert_to_mp3(input_file, output_file):
    """
    将音频部分转换为 MP3 格式。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,        # 输入文件
                "-vn",                   # 去掉视频流
                "-acodec", "libmp3lame", # 指定 MP3 编码器
                "-q:a", "2",             # 设置编码质量（2 表示高质量）
                output_file
            ],
            check=True
        )
        print(f"已转换为 MP3: '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败 '{input_file}'：{e}")
        return False


def extract_audio(input_file, output_file):
    """
    尝试直接提取保留原始音频格式。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,       # 输入文件
                "-vn",                  # 去掉视频流
                "-acodec", "copy",      # 直接复制音频流
                output_file
            ],
            check=True
        )
        print(f"已提取并保留原始音频格式: '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取音频失败 '{input_file}'：{e}")
        return False


def process_file(file_name):
    """
    处理单个文件，根据格式决定处理方法。
    """
    base_name, ext = os.path.splitext(file_name)  # 分离文件名和扩展名
    repaired_file = os.path.join(output_dir, f"{base_name}_repaired{ext}")
    output_mp3_path = os.path.join(output_dir, f"{base_name}.mp3")
    
    # 修复文件
    if not is_valid_media_file(file_name):
        print(f"文件 '{file_name}' 无效，跳过处理...")
        return

    if not repair_file(file_name, repaired_file):
        print(f"无法修复 '{file_name}'，跳过...")
        return
    
    # 获取音频流格式
    audio_format = get_audio_format(repaired_file)

    if audio_format:
        if audio_format == "cook":
            # 针对 'cook' 音频，转换为 MP3
            print(f"检测到 'cook' 格式音频: {file_name}，开始转换为 MP3...")
            convert_to_mp3(repaired_file, output_mp3_path)
        else:
            # 对其他音频，尝试直接提取为原格式
            output_format_path = os.path.join(output_dir, f"{base_name}.{audio_format}")
            print(f"检测到 '{audio_format}' 格式音频: {file_name}，尝试直接提取...")
            if not extract_audio(repaired_file, output_format_path):
                print(f"直接提取音频失败 '{file_name}'，改为转 MP3。")
                convert_to_mp3(repaired_file, output_mp3_path)
    else:
        # 如果无法识别音频格式，尝试直接转为 MP3
        print(f"无法识别 '{file_name}' 的音频格式，尝试直接转换为 MP3...")
        convert_to_mp3(repaired_file, output_mp3_path)


# 遍历当前目录中的所有文件
for file_name in os.listdir("."):
    if os.path.isfile(file_name) and not file_name.endswith(".py"):  # 排除脚本文件本身
        print(f"正在处理文件: {file_name}")
        process_file(file_name)

print(f"音频处理完成！所有结果已保存到 '{output_dir}' 文件夹中。")
