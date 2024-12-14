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

def get_audio_streams(video_file):
    """
    使用 ffprobe 获取视频文件中的所有音频流信息。
    返回音频流的索引及其格式。
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index,codec_name", "-of", "json", video_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        probe_data = json.loads(result.stdout)
        if "streams" in probe_data and probe_data["streams"]:
            return [(stream["index"], stream["codec_name"]) for stream in probe_data["streams"]]
        else:
            print(f"文件 '{video_file}' 不包含音频流！")
            return []
    except json.JSONDecodeError:
        print(f"无法分析文件 '{video_file}' 的格式，可能不是有效的音频/视频文件。")
        return []
    except Exception as e:
        print(f"解析文件 '{video_file}' 音频格式时出错：{e}")
        return []

def extract_audio_by_stream(input_file, stream_index, audio_format, output_file):
    """
    直接提取指定音频流，并生成对应的音频文件。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,       # 输入文件
                "-map", f"0:{stream_index}",  # 仅提取指定音频流
                "-acodec", "copy",      # 直接复制音频流
                output_file
            ],
            check=True
        )
        print(f"已提取音轨 {stream_index} 并保留格式 '{audio_format}': '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取音轨 {stream_index} 失败 '{input_file}'：{e}")
        return False

def convert_to_mp3(input_file, stream_index, output_file):
    """
    提取指定音频流并转换为 MP3 格式。
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_file,       # 输入文件
                "-map", f"0:{stream_index}",  # 仅提取指定音频流
                "-acodec", "libmp3lame", # 指定 MP3 编码器
                "-q:a", "2",            # 设置编码质量（2 表示高质量）
                output_file
            ],
            check=True
        )
        print(f"已转换为 MP3: [{stream_index}] '{input_file}' -> '{output_file}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败 [{stream_index}] '{input_file}'：{e}")
        return False

def delete_empty_file(file_path):
    """
    如果文件大小为 0，删除该文件。
    """
    if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
        try:
            os.remove(file_path)
            print(f"已删除大小为 0 的文件: {file_path}")
            return True
        except Exception as e:
            print(f"无法删除空文件 '{file_path}'：{e}")
    return False

def process_file(file_name):
    """
    处理单个文件，根据音频流格式决定处理方法。
    """
    base_name, ext = os.path.splitext(file_name)  # 分离文件名和扩展名

    # 检查文件有效性
    if not is_valid_media_file(file_name):
        print(f"文件 '{file_name}' 无效，跳过处理...")
        return

    # 获取音频流信息
    audio_streams = get_audio_streams(file_name)

    if not audio_streams:
        print(f"文件 '{file_name}' 无法找到有效的音频流，跳过处理...")
        return

    for stream_index, audio_format in audio_streams:
        if audio_format == "aac":
            # 针对 'aac' 音频，直接提取为 m4a
            output_format_path = os.path.join(output_dir, f"{base_name}_track{stream_index}.m4a")
            print(f"检测到流 {stream_index} 是 'aac': {file_name}，直接提取为 m4a...")
            if not extract_audio_by_stream(file_name, stream_index, audio_format, output_format_path):
                print(f"提取 'aac' 音轨失败，将尝试转换为 MP3...")
                output_mp3_path = os.path.join(output_dir, f"{base_name}_track{stream_index}.mp3")
                convert_to_mp3(file_name, stream_index, output_mp3_path)
        else:
            # 对非 'aac' 格式，尝试提取原始音频格式
            output_format_path = os.path.join(output_dir, f"{base_name}_track{stream_index}.{audio_format}")
            print(f"检测到流 {stream_index} 格式为 '{audio_format}': {file_name}，尝试直接提取...")
            if not extract_audio_by_stream(file_name, stream_index, audio_format, output_format_path):
                print(f"直接提取音轨 {stream_index} 失败，检查文件并转换为 MP3...")
                # 如果提取失败并生成了空文件，则删除
                if delete_empty_file(output_format_path):
                    print(f"音轨 {stream_index} 的提取失败文件已删除。")
                # 转换流为 MP3
                output_mp3_path = os.path.join(output_dir, f"{base_name}_track{stream_index}.mp3")
                convert_to_mp3(file_name, stream_index, output_mp3_path)

# 遍历当前目录中的所有文件
for file_name in os.listdir("."):
    if os.path.isfile(file_name) and not file_name.endswith(".py"):  # 排除脚本文件本身
        print(f"正在处理文件: {file_name}")
        process_file(file_name)

print(f"音频处理完成！所有结果已保存到 '{output_dir}' 文件夹中。")