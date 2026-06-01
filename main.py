import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from search_api import fetch_search_results, get_organizations

def format_time(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    milliseconds = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def on_search():
    keyword = entry_keyword.get().strip()
    if not keyword:
        messagebox.showwarning("提示", "请输入搜索关键词")
        return
    
    selected_orgs = [org_id for org_id, var in org_vars.items() if var.get()]
    if not selected_orgs:
        messagebox.showwarning("提示", "请至少选择一个组织")
        return
    
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"正在搜索关键词: {keyword}...\n")
    result_text.insert(tk.END, f"选择的组织: {', '.join([get_organizations()[org_id]['name'] for org_id in selected_orgs])}\n\n")
    root.update()
    
    results = fetch_search_results(keyword, selected_orgs)
    
    if "error" in results:
        result_text.insert(tk.END, f"搜索失败: {results['error']}")
        return
    
    if "data" in results and "items" in results["data"]:
        items = results["data"]["items"]
        pagination = results["data"].get("pagination", {})
        
        result_text.insert(tk.END, f"搜索结果: 共 {len(items)} 条数据\n")
        result_text.insert(tk.END, "-" * 50 + "\n\n")
        
        for i, item in enumerate(items, 1):
            title = item.get("title", "无标题")
            datetime = item.get("datetime", "无时间")
            author_name = item.get("author", {}).get("name", "未知作者")
            play_url = item.get("play_url", "")
            org_name = item.get("org_name", "")
            clip_id = item.get("id", "")
            subtitles = item.get("subtitles", [])
            
            result_text.insert(tk.END, f"【{i}】{title}\n")
            if org_name:
                result_text.insert(tk.END, f"  组织: {org_name}\n")
            result_text.insert(tk.END, f"  作者: {author_name}\n")
            result_text.insert(tk.END, f"  时间: {datetime}\n")
            result_text.insert(tk.END, f"  视频ID: {clip_id}\n")
            if play_url:
                result_text.insert(tk.END, f"  链接: {play_url}\n")
            
            if subtitles:
                result_text.insert(tk.END, f"  匹配的字幕 ({len(subtitles)}条):\n")
                for sub in subtitles:
                    start_time = format_time(sub.get("start", 0))
                    end_time = format_time(sub.get("end", 0))
                    clean_content = sub.get("clean_content", "")
                    pinyin = sub.get("pinyin", "")
                    text = sub.get("text", "")
                    
                    result_text.insert(tk.END, f"    - [{start_time} ~ {end_time}] ")
                    
                    temp_content = clean_content
                    if pinyin:
                        start_idx = temp_content.find(pinyin)
                        if start_idx != -1:
                            result_text.insert(tk.END, temp_content[:start_idx])
                            result_text.insert(tk.END, pinyin, "pinyin_tag")
                            temp_content = temp_content[start_idx + len(pinyin):]
                    
                    if text:
                        start_idx = temp_content.find(text)
                        if start_idx != -1:
                            result_text.insert(tk.END, temp_content[:start_idx])
                            result_text.insert(tk.END, text, "text_tag")
                            temp_content = temp_content[start_idx + len(text):]
                    
                    result_text.insert(tk.END, temp_content)
                    result_text.insert(tk.END, "\n")
            
            result_text.insert(tk.END, "\n")
        
        if pagination:
            result_text.insert(tk.END, "-" * 50 + "\n")
            result_text.insert(tk.END, f"分页信息: 第{pagination.get('page', 1)}页 / 共{pagination.get('total_pages', 1)}页\n")
            result_text.insert(tk.END, f"总数据量: {pagination.get('total', 0)}条\n")
    
    else:
        result_text.insert(tk.END, "未找到相关数据")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("搜索工具")
    root.geometry("900x700")

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    label_keyword = ttk.Label(frame, text="搜索关键词:")
    label_keyword.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

    entry_keyword = ttk.Entry(frame, width=50)
    entry_keyword.grid(row=0, column=1, padx=5, pady=5)
    entry_keyword.bind("<Return>", lambda event: on_search())

    btn_search = ttk.Button(frame, text="搜索", command=on_search)
    btn_search.grid(row=0, column=2, padx=5, pady=5)

    label_org = ttk.Label(frame, text="选择组织(支持多选):")
    label_org.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

    org_frame = ttk.Frame(frame)
    org_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

    organizations = get_organizations()
    org_vars = {}
    
    for i, (org_id, org_info) in enumerate(organizations.items()):
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(org_frame, text=org_info["name"], variable=var)
        chk.pack(side=tk.LEFT, padx=10)
        org_vars[org_id] = var

    result_text = scrolledtext.ScrolledText(frame, width=100, height=35, wrap=tk.WORD)
    result_text.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky=tk.W+tk.E+tk.N+tk.S)
    
    result_text.tag_configure("pinyin_tag", foreground="red")
    result_text.tag_configure("text_tag", foreground="blue")

    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)

    root.mainloop()