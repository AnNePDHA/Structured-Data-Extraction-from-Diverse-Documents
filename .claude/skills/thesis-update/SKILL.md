---
name: thesis-update
description: >
  Tự động đọc conversation hiện tại, lọc ra những nội dung đã được chốt, tổng hợp thành bản preview để người dùng confirm, rồi ghi thẳng vào đúng chương, mục trong paper/thesis.tex theo đúng style luận văn thạc sĩ Bách Khoa.

  LUÔN dùng skill này khi người dùng nói: "update luận văn", "ghi vào thesis", "append vào report", "update latex", "lưu lại những gì đã chốt", "sync vào paper", hoặc bất kỳ yêu cầu nào liên quan đến ghi nội dung từ conversation vào file luận văn. Cũng gợi ý dùng skill này khi một conversation dài về một section cụ thể vừa kết thúc.
---

# Thesis Update Skill

Skill này áp dụng cho luận văn: **"Xây dựng hệ thống trích xuất dữ liệu có cấu trúc từ đa dạng tài liệu và đánh giá hiệu năng các mô hình VLM và OCR-LLM"** — Phạm Đại Hoàng An, Bách Khoa ĐHQG TP.HCM.

---

## Cấu trúc thư mục

```
LVTN/
├── outline/
│   ├── THESIS_CONTEXT.md               ← context tổng thể
│   ├── WRITING_STYLE.md                ← style guide (đã embed vào skill này)
│   └── DATASOURCE_CONTEXT.md           ← nguồn và trạng thái dữ liệu
└── paper/
    └── thesis.tex                      ← nguồn duy nhất của nội dung chương
```

Không còn file outline `.md` theo chương. Mọi nội dung chương ghi thẳng vào `thesis.tex`.

---

## Quy trình thực hiện

### Bước 1 — Scan conversation, lọc "đã chốt"

Đọc toàn bộ lịch sử conversation. Chỉ giữ lại nội dung **đã chốt**, tức là:

**Lấy vào:**
- Kết luận được confirm rõ ràng ("vậy dùng X", "ok chốt rồi", "✅", "đúng rồi")
- Định nghĩa / framing đã được thống nhất
- Số liệu, kết quả benchmark đã verify
- Quyết định kỹ thuật đã được xác nhận
- Mô tả phương pháp/kiến trúc đã agree

**Bỏ qua:**
- Câu hỏi còn mở ("hay là...", "chưa chắc", "cần check lại")
- Ideas đang thảo luận, chưa kết luận
- Alternatives đã bị loại
- Nội dung brainstorm chưa được chốt

### Bước 2 — Detect section

Map nội dung đã chốt vào đúng `\chapter{}` / `\section{}` của `paper/thesis.tex`:

| Chương trong thesis.tex | Nội dung |
|------|---------|
| `\chapter{Giới thiệu}` | Đặt vấn đề, Mục tiêu, Phạm vi, Đóng góp, Tổng quan |
| `\chapter{Công trình liên quan}` | Các công trình liên quan, OCR-LLM, VLM, Benchmark, Research gap |
| `\chapter{Cơ sở lý thuyết}` | IDP, OCR, LLM, VLM, Structured Extraction, Metrics |
| `\chapter{Phương pháp đề xuất}` | Kiến trúc hệ thống, Dataset, Pipeline A/B, Kết quả, Thiết kế hệ thống |
| `\chapter{Kết luận}` | Nhận xét, Hạn chế, Hướng phát triển |

Một conversation thường span nhiều section — gom tất cả lại, không chỉ lấy section chính. Nếu cấu trúc chương đã đổi (ví dụ tách chương hệ thống riêng), lấy danh sách `\chapter` thực tế trong `thesis.tex` làm chuẩn.

### Bước 3 — Đọc vị trí đích

Đọc `\section{}` tương ứng trong `thesis.tex` để:
- Nắm nội dung đã có, tránh trùng lặp
- Xác định vị trí insert phù hợp (cuối section nào, sau đoạn nào)

### Bước 4 — Tổng hợp preview (BẮT BUỘC, không skip)

Hiển thị cho người dùng xem trước, **group theo chương** để dễ review:

```
📋 Tìm thấy [N] điểm cần update vào [M] chương:

📄 Chương 2 — Công trình liên quan
  1. [Tóm tắt ý — 1 câu] → Section 2.X
  2. [Tóm tắt ý — 1 câu] → Section 2.Y

📄 Chương 4 — Phương pháp đề xuất
  3. [Tóm tắt ý — 1 câu] → Section 4.X

Confirm tất cả? Hoặc chỉnh: "bỏ ý 3", "ý 2 vào 3.2 thay vì 3.1", "bỏ chương 4 lần này"...
```

Chờ người dùng confirm trước khi ghi bất cứ thứ gì. Sau khi confirm → update **lần lượt từng chương** theo thứ tự, báo cáo xong từng chương trước khi sang chương tiếp theo.

### Bước 5 — Update thesis.tex

Mở `LVTN/paper/thesis.tex`, tìm đúng `\chapter{}` / `\section{}` và insert nội dung mới vào đúng vị trí, theo đúng LaTeX style bên dưới.

**Quan trọng:** Đây là file duy nhất chứa toàn bộ luận văn — đọc kỹ context xung quanh vị trí insert để đảm bảo nội dung mới liền mạch với phần trước và sau.

### Bước 6 — Ghi changelog

Nếu nội dung vừa ghi là một quyết định về scope, mô hình, dataset, mục lục hoặc phản hồi của GVHD, thêm một dòng vào Mục 15 (Changelog) của `outline/THESIS_CONTEXT.md`.

---

## Style Guide — Embedded từ WRITING_STYLE.md

### Xưng hô
- Chương 1: dùng **"tôi"** (quan điểm cá nhân)
- Chương 2, 3, 4, 5: dùng **"tác giả"**
- Tuyệt đối không dùng "chúng tôi" hay "nhóm tác giả"

### Câu mở đầu chương
```latex
% Template chuẩn
Trong chương này, tác giả sẽ [động từ] [nội dung chương].
```

### Thuật ngữ song ngữ
Lần đầu xuất hiện: `[Tiếng Việt] ([Tiếng Anh] - [Viết tắt])`
Ví dụ: *"Mô hình ngôn ngữ lớn (Large Language Model - LLM)"*
Từ lần 2 trở đi: chỉ dùng viết tắt hoặc tên tiếng Anh.

### Định nghĩa kỹ thuật — 3 bước
```latex
% Bước 1: Định nghĩa trích dẫn
\emph{"[Định nghĩa nguyên văn tiếng Anh]" \cite{key}.}

% Bước 2: Giải thích tiếng Việt (1–2 câu)

% Bước 3: Đặc điểm (itemize với \textbf{})
\begin{itemize}
    \item \textbf{Tên đặc điểm}: Giải thích...
\end{itemize}
```

### Danh sách
```latex
% Liệt kê đặc điểm → itemize, từ khóa in đậm
\begin{itemize}
    \item \textbf{Tên}: Giải thích 1–4 câu.
\end{itemize}

% Bước quy trình → enumerate
\begin{enumerate}
    \item Bước 1...
\end{enumerate}
```

### Nhận xét công trình liên quan (Chương 2)
```latex
\paragraph{Nhận xét:}
[2–4 câu về ưu điểm, phạm vi, kết quả nổi bật]

% Chỉ dùng cho công trình quan trọng:
\subsection*{Nhược điểm của phương pháp [Tên]}
\begin{enumerate}
    \item \textbf{Tên nhược điểm}: ...
\end{enumerate}
```

### Công thức
```latex
% Công thức đơn có đánh số
\begin{equation}
    ...
\end{equation}
Trong đó:
\begin{itemize}
    \item $X$: Ý nghĩa của X,
\end{itemize}

% Bộ công thức (Precision/Recall/F1...) → \[...\], mỗi cái một dòng
\[...\]
\[...\]
```

### Hình ảnh & Bảng
```latex
% Hình
\begin{figure}[!h]
    \centering
    \includegraphics[width=0.8\linewidth]{Images/ten_hinh.png}
    \caption{Mô tả nội dung hình}
    \label{fig:ten_nhan}
\end{figure}

% Bảng — caption TRÊN bảng
\begin{table}[h]
\centering
\caption{Tên bảng}
\label{tab:ten_nhan}
\begin{tabular}{|l|c|c|}
\hline
\textbf{Cột 1} & \textbf{Cột 2} & \textbf{Cột 3} \\ \hline
...
\end{tabular}
\end{table}
```

### Trích dẫn
```latex
% Paper
[Khái niệm]\cite{key}

% Tool/URL
[Tên tool]\footnotemark
\footnotetext{[Tên] \url{https://...}}
```

### Cross-reference
```latex
% LUÔN dùng \hyperref, không bao giờ viết "như đã nói ở trên"
...được trình bày ở \hyperref[sec:ten]{Mục X.Y}.
```

### Code
```latex
% JSON, Python phức tạp → minted
\begin{minted}{json}...\end{minted}

% SQL, Cypher → lstlisting
\begin{lstlisting}[language=SQL]...\end{lstlisting}

% Lệnh đơn giản → verbatim
\begin{verbatim}...\end{verbatim}
```

### Tông văn phong
- **Dùng:** "Phương pháp này cho phép...", "Kết quả thực nghiệm cho thấy...", "Tác giả đề xuất...", "Có thể nhận thấy rằng..."
- **Tránh:** "Rất tốt" → dùng số liệu cụ thể; "Như đã nói ở trên" → dùng `\hyperref`; "Hiển nhiên là..." → chứng minh thay vì khẳng định
- Mỗi câu 20–50 từ, mỗi đoạn 3–7 câu

### Cấu trúc section Chương 3 (Cơ sở lý thuyết)
```
Định nghĩa (\emph{} + \cite{})
→ Giải thích tiếng Việt (2–3 câu)
→ Đặc điểm chính (itemize + \textbf{})
→ Ví dụ / Hình minh họa
→ Liên hệ với đề tài (1–2 câu)
```

### Cấu trúc công trình Chương 2 (Related Work)
```
Giới thiệu ngắn (1 câu)
→ Phương pháp / Kiến trúc
→ Hình (nếu có)
→ Kết quả / Bảng (nếu có)
→ \paragraph{Nhận xét:}
→ \subsection*{Nhược điểm} (chỉ công trình quan trọng)
```

---

## LaTeX Conventions — Tiêu đề section

Preamble `thesis.tex` đã có `titlesec` + `\raggedright` → tiêu đề tự wrap, không overflow:
```latex
\titleformat*{\section}{\Large\bfseries\raggedright}
\titleformat*{\subsection}{\large\bfseries\raggedright}
```
- **Không** thêm `\\` thủ công trong `\section{}` hay `\subsection{}`.
- Tiêu đề dài: dùng `\section[tên ngắn cho TOC]{Tên đầy đủ}`.
- `\cite{}` **không** đặt trong `\section{}` → ra `[?]`. Đặt cite trong thân văn bản.
- URL/tool không có paper: dùng `\protect\footnote{\url{...}}` bên trong `\section{}`.

---

## Nguyên tắc bất biến

1. **Không hallucinate** — chỉ ghi những gì thực sự có trong conversation. Nếu không rõ kết quả, ghi `% TODO: chưa xác nhận`
2. **Không trùng lặp** — đọc section đích trong `thesis.tex` trước, không ghi nội dung đã có
3. **Không skip bước confirm** — luôn show preview, luôn chờ người dùng ok
4. **Nhất quán thuật ngữ** — kiểm tra cách đã dùng trong file hiện tại, dùng lại đúng cách đó
5. **Cite key** — nếu conversation nhắc đến paper đã có trong `THESIS_CONTEXT.md` (Mục 10), dùng đúng tên paper để đặt cite key tạm (vd: `\cite{huang2019sroie}`)
