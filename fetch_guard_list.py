import requests
import csv
import os
from datetime import datetime
import time

def fetch_all_guard_pages(roomid, ruid):
    """
    遍历所有页面获取完整舰长名单
    """
    base_url = "https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topList"
    page_size = 10
    page = 1
    all_guards = []
    seen_uids = set()  # 用于内存中去重
    
    try:
        while True:
            print(f"正在获取第 {page} 页...")
            
            params = {
                "roomid": roomid,
                "page": page,
                "ruid": ruid,
                "page_size": page_size
            }
            
            # 添加请求头模拟浏览器访问
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://live.bilibili.com"
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] != 0:
                print(f"API返回错误: {data['message']}")
                break
            
            # 合并top3和list中的数据
            guard_list = data["data"]["list"]
            if page == 1 and "top3" in data["data"]:
                guard_list.extend(data["data"]["top3"])
            
            current_page = data["data"]["info"]["page"]
            total_pages = data["data"]["info"]["page"]
            
            # 处理当前页数据，去重
            for guard in guard_list:
                uid = guard["uid"]
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    guard["fetch_date"] = datetime.now().strftime("%Y-%m-%d")
                    all_guards.append(guard)
            
            print(f"第 {page} 页获取到 {len(guard_list)} 条记录，已去重累计 {len(all_guards)} 条")
            
            # 检查是否还有更多页面
            if page >= total_pages:
                break
                
            page += 1
            time.sleep(1)  # 礼貌性延迟，避免请求过快
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
    except Exception as e:
        print(f"程序执行出错: {e}")
    
    return all_guards

def save_to_csv(guards, filename="guard_list.csv"):
    """
    将舰长数据增量保存到CSV文件
    """
    if not guards:
        print("没有获取到新数据，跳过保存")
        return False
    
    # 定义CSV文件的列顺序
    fieldnames = [
        "fetch_date", "uid", "username", "rank", 
        "guard_level", "accompany", "face",
        "medal_name", "medal_level", "ruid"
    ]
    
    file_exists = os.path.exists(filename)
    existing_uids = set()
    
    # 如果文件已存在，读取已有UID进行去重
    if file_exists:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'uid' in row:
                        existing_uids.add(int(row['uid']))
            print(f"已从现有文件读取 {len(existing_uids)} 条已有记录")
        except Exception as e:
            print(f"读取现有文件出错: {e}")
    
    # 过滤掉已存在的UID
    new_guards = []
    for guard in guards:
        if guard["uid"] not in existing_uids:
            # 格式化数据，确保所有字段都存在
            formatted_guard = {
                "fetch_date": guard.get("fetch_date", ""),
                "uid": guard.get("uid", ""),
                "username": guard.get("username", ""),
                "rank": guard.get("rank", ""),
                "guard_level": guard.get("guard_level", ""),
                "accompany": guard.get("accompany", ""),
                "face": guard.get("face", ""),
                "medal_name": guard.get("medal_info", {}).get("medal_name", ""),
                "medal_level": guard.get("medal_info", {}).get("medal_level", ""),
                "ruid": guard.get("ruid", "")
            }
            new_guards.append(formatted_guard)
    
    if not new_guards:
        print("没有新的唯一记录需要添加")
        return False
    
    # 写入CSV文件（追加模式）
    mode = 'a' if file_exists else 'w'
    with open(filename, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # 如果是新文件，写入表头
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(new_guards)
    
    print(f"成功保存 {len(new_guards)} 条新记录到 {filename}")
    return True

def check_user_is_guard(uid_to_check, guards):
    """
    检查指定UID是否为舰长
    """
    for guard in guards:
        if guard["uid"] == uid_to_check:
            return {
                "is_guard": True,
                "username": guard["username"],
                "rank": guard["rank"],
                "guard_level": guard["guard_level"]
            }
    return {"is_guard": False}

def main():
    """主函数"""
    # 配置参数（可以从环境变量或外部传入）
    ROOM_ID = 92613
    RU_ID = 13046
    OUTPUT_FILE = "guard_list.csv"
    
    # 要检查的用户UID（示例，可根据需要修改）
    TARGET_UID = 9035305  # 示例UID，来自API返回数据
    
    print(f"开始获取房间 {ROOM_ID} 的舰长名单...")
    print(f"主播RU_ID: {RU_ID}")
    print("=" * 50)
    
    # 获取所有舰长数据
    guards = fetch_all_guard_pages(ROOM_ID, RU_ID)
    
    if guards:
        print(f"\n总计获取到 {len(guards)} 条唯一舰长记录")
        
        # 检查目标用户是否为舰长
        check_result = check_user_is_guard(TARGET_UID, guards)
        if check_result["is_guard"]:
            print(f"\n✅ 用户 {TARGET_UID} 是舰长！")
            print(f"   用户名: {check_result['username']}")
            print(f"   排名: {check_result['rank']}")
            print(f"   舰长等级: {check_result['guard_level']}")
        else:
            print(f"\n❌ 用户 {TARGET_UID} 不是舰长")
        
        # 保存到CSV文件
        save_to_csv(guards, OUTPUT_FILE)
        
        # 输出统计信息
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1  # 减去表头
            print(f"\n📊 CSV文件总计记录: {line_count} 条")
    else:
        print("未能获取到舰长数据")

if __name__ == "__main__":
    main()
