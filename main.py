import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
from extractor import select_pdf_file, extract_text_from_pdf, get_scholar_keywords
from translator import translate_full_text, set_api_key, robust_translate_text_segment
import tiktoken
import re

def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    return len(tokens)

def estimate_cost(tokens: int, multiplier: float = 1.0):
    total_tokens = tokens * (1 + multiplier)
    cost35 = total_tokens / 1000 * 0.002
    cost_4 = total_tokens / 1000 * 0.06
    return cost35, cost_4

def ask_model_choice(tokens: int):
    cost35, cost_4 = estimate_cost(tokens)
    msg = (f"총 토큰 수: {tokens}\n"
           f"GPT 3.5-turbo(일반형) 예상 비용: 약 ${cost35:.4f}\n"
           f"GPT 4(정밀형) 예상 비용: 약 ${cost_4:.4f}\n\n"
           "번역을 진행할까요? 아래에서 사용할 모델을 선택하세요.")
    
    dialog = tk.Toplevel()
    dialog.title("모델 선택")
    dialog.resizable(False, False)

    label = tk.Label(dialog, text=msg, justify="left")
    label.pack(padx=20, pady=10)
    
    choice = tk.StringVar(value="gpt-3.5-turbo")
    rb35 = tk.Radiobutton(dialog, text="GPT-3.5-turbo", variable=choice, value="gpt-3.5-turbo")
    rb4 = tk.Radiobutton(dialog, text="GPT-4", variable=choice, value="gpt-4")
    rb35.pack(anchor="w", padx=20)
    rb4.pack(anchor="w", padx=20)

    result = {}

    def on_ok():
        result["model"] = choice.get()
        dialog.destroy()

    def on_cancel():
        result["model"] = None
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)
    ok_btn = tk.Button(button_frame, text="확인", width=10, command=on_ok)
    ok_btn.pack(side="left", padx=5)
    cancel_btn = tk.Button(button_frame, text="취소", width=10, command=on_cancel)
    cancel_btn.pack(side="left", padx=5)

    dialog.grab_set()
    dialog.wait_window()

    return result.get("model")

def split_into_pages(text: str) -> list:
    pages = re.split(r"\[page \d+\]", text)
    return [page.strip() for page in pages if page.strip()]


def translate_full_text_with_progress(full_text, target_lang="한국어", model="gpt-3.5-turbo", master=None):
    page_marker_re = re.compile(r'(\[page\s*\d+\])', re.IGNORECASE)

    parts = page_marker_re.split(full_text)
    pages = []
    current_marker = ""
    current_body = ""
    for part in parts:
        part = part.strip()
        if page_marker_re.fullmatch(part):
            if current_marker or current_body:
                pages.append(f"{current_marker}\n\n{current_body.strip()}")
            current_marker = part
            current_body = ""
        else:
            current_body += part + "\n\n"
    # 마지막 블록 추가
    if current_marker or current_body:
        pages.append(f"{current_marker}\n\n{current_body.strip()}")

    total = len(pages)
    translated_pages = [""] * total

    # 3) 진행 창 생성
    prog_win = tk.Toplevel(master)
    prog_win.title("번역 진행 중")
    prog_win.resizable(False, False)
    label = tk.Label(prog_win, text=f"번역 진행: 0 / {total}")
    label.pack(padx=10, pady=5)
    progress_bar = ttk.Progressbar(prog_win, orient="horizontal",
                                   length=300, mode="determinate",
                                   maximum=total)
    progress_bar.pack(padx=10, pady=5)

    def translate_next_page(index):
        if index >= total:
            prog_win.destroy()
            return

        raw = pages[index]
        m = page_marker_re.match(raw)
        if m:
            marker = m.group(1)
            body = raw[m.end():].strip()
        else:
            marker, body = "", raw

        if body:
            try:
                translated_body = robust_translate_text_segment(
                    body, target_lang=target_lang, model=model
                )
            except Exception as e:
                translated_body = f"오류 발생: {e}"
        else:
            translated_body = ""

        # 마커 + 번역문 결합
        translated_pages[index] = (
            (marker + "\n\n") if marker else ""
        ) + translated_body

        # 진행 표시 업데이트
        label.config(text=f"번역 진행: {index+1} / {total}")
        progress_bar.step(1)
        prog_win.after(100, lambda: translate_next_page(index+1))

    #  호출
    prog_win.after(100, lambda: translate_next_page(0))
    prog_win.wait_window()

    # 합치기
    return "\n\n".join(translated_pages)


def main():
    root = tk.Tk()
    root.withdraw()
    root.title('PDF Translator')
    # API 키 설정 (환경변수 또는 사용자 입력)
    set_api_key(master = root)
    
    # PDF 파일 선택 및 학자 키워드 입력 (옵션)
    pdf_file = select_pdf_file(master = root)
    if not pdf_file:
        messagebox.showerror("오류", "PDF 파일이 선택되지 않았습니다.", parent=root)
        root.destroy()
        return

    detect_words = get_scholar_keywords(master=root)
    if detect_words:
        print("입력된 학자 키워드:", detect_words)
    else:
        print("학자 키워드가 입력되지 않았습니다. 해당 검출 기능은 건너뜁니다.")
    
    # PDF 텍스트 추출 (detect_words를 함께 전달)
    full_text, tags, file_basename = extract_text_from_pdf(pdf_file, detect_words, master=root)
    if full_text is None:
        messagebox.showerror("오류", "텍스트 추출에 실패했습니다.", parent=root)
        root.destroy()
        return
    
    extracted_text_file = f"{file_basename}_text.txt"
    with open(extracted_text_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"PDF 텍스트 추출 완료: {extracted_text_file}")

    try:
        tokens = count_tokens(full_text, model_name="gpt-3.5-turbo")
    except Exception as e:
        messagebox.showerror("계산 오류", str(e), parent=root)
        root.destroy()
        return
    print("토큰 수:", tokens)

    chosen_model = ask_model_choice(tokens)
    if not chosen_model:
        messagebox.showinfo("취소", "번역 진행 취소.", parent=root)
        root.destroy()
        return
    print("모델:", chosen_model)

    # # 토큰 수 계산 및 비용 예측, 그리고 사용 모델 선택
    # chosen_model = ask_model_choice(tokens)
    
    translated_text = translate_full_text_with_progress(
        full_text, 
        target_lang="한국어", 
        model=chosen_model, 
        master=root
        )
    translated_text_file = f"{file_basename}_translated.txt"
    with open(translated_text_file, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"번역 완료: {translated_text_file}")
    
    messagebox.showinfo("완료", f"번역이 완료되었습니다!\n파일: {translated_text_file}", parent=root)
    root.destroy()

if __name__ == "__main__":
    main()
