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
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "json", video_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        probe_data = json.loads(result.stdout)
        if "streams" in probe_data and probe_data["streams"]:
            return probe_data["streams"][0]["codec_name"]
        else:
            print(f"文件 '{video_file}' 不包含音频流！")
            return None
    except json.JSONDecodeError:
        print(f"无法分析文件 '{video_file}' 的格式，可能不是有效的音频/视频文件。")
        return None
    except IndexError:
        print(f"文件 '{video_file}' 中没有音频流！")
        return None
    except Exception as e:
        print(f"解析文件 '{video_file}' 音频格式时出错：{e}")
        return None

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
    output_audio_path = os.path.join(output_dir, f"{base_name}.mp3")
    
    # 检查文件有效性
    if not is_valid_media_file(file_name):
        print(f"文件 '{file_name}' 无效，跳过处理...")
        return
    
    # 获取音频流格式
    audio_format = get_audio_format(file_name)

    if audio_format:
        if audio_format == "cook":
            # 针对 'cook' 音频，转换为 MP3
            print(f"检测到 'cook' 格式音频: {file_name}，开始转换为 MP3...")
            convert_to_mp3(file_name, output_audio_path)
        else:
            # 对其他音频，尝试直接提取为原格式
            output_format_path = os.path.join(output_dir, f"{base_name}.{audio_format}")
            print(f"检测到 '{audio_format}' 格式音频: {file_name}，尝试直接提取...")
            if not extract_audio(file_name, output_format_path):
                print(f"直接提取音频失败 '{file_name}'，改为转 MP3。")
                convert_to_mp3(file_name, output_audio_path)
    else:
        # 如果无法识别音频格式，尝试直接转为 MP3
        print(f"无法识别 '{file_name}' 的音频格式，尝试直接转换为 MP3...")
        convert_to_mp3(file_name, output_audio_path)


# 遍历当前目录中的所有文件
for file_name in os.listdir("."):
    if os.path.isfile(file_name) and not file_name.endswith(".py"):  # 排除脚本文件本身
        print(f"正在处理文件: {file_name}")
        process_file(file_name)

print(f"音频处理完成！所有结果已保存到 '{output_dir}' 文件夹中。")
