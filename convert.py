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

def extract_audio_to_m4a(input_file, output_file):
    """
    提取音频并封装为 M4A 格式。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,           # 输入文件
                "-vn",                      # 去掉视频流
                "-acodec", "copy",          # 保持原始音频格式
                output_file                 # 输出为 M4A 文件
            ],
            check=True
        )
        print(f"已提取并封装为 M4A: '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取音频失败 '{input_file}'：{e}")
        return False

def convert_to_mp3(input_file, output_file):
    """
    如果无法直接提取音频，则将音频部分重新编码为 MP3。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,
                "-vn",                  # 去掉视频流
                "-acodec", "libmp3lame",
                "-q:a", "2",            # 设置编码质量（2 表示高质量）
                output_file
            ],
            check=True
        )
        print(f"已转换为 MP3: '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败 '{input_file}'：{e}")
        return False

def process_file(file_name):
    """
    处理单个文件，提取音频并直接保存为 M4A 格式。
    如果失败则尝试转为 MP3。
    """
    base_name = os.path.splitext(file_name)[0]  # 分离文件名和扩展名
    output_audio_path_m4a = os.path.join(output_dir, f"{base_name}.m4a")
    output_audio_path_mp3 = os.path.join(output_dir, f"{base_name}.mp3")
    
    # 检查文件有效性
    if not is_valid_media_file(file_name):
        print(f"文件 '{file_name}' 无效，跳过处理...")
        return
    
    # 提取音频并封装为 M4A
    if not extract_audio_to_m4a(file_name, output_audio_path_m4a):
        print(f"直接提取音频失败 '{file_name}'，改为转 MP3。")
        convert_to_mp3(file_name, output_audio_path_mp3)

# 遍历当前目录中的所有文件
for file_name in os.listdir("."):
    if os.path.isfile(file_name) and not file_name.endswith(".py"):  # 排除脚本文件本身
        print(f"正在处理文件: {file_name}")
        process_file(file_name)

print(f"音频处理完成！所有结果已保存到 '{output_dir}' 文件夹中。")