# Phong cách & Tông viết Luận văn Thạc sĩ

> Tổng hợp từ luận văn mẫu `main.tex` (Lê Nguyên Khang, Graph RAG, Bách Khoa ĐHQG TP.HCM).
> Áp dụng khi viết luận văn: *Xây dựng hệ thống trích xuất dữ liệu có cấu trúc từ đa dạng tài liệu và đánh giá hiệu năng các mô hình VLM và OCR-LLM*.

---

## 1. Xưng hô & Ngôi kể

- Dùng **"tác giả"** (ngôi thứ ba) là chính, đặc biệt ở Chương 2, 3, 4.
- Dùng **"tôi"** ở Chương 1 (Đặt vấn đề, Phạm vi nghiên cứu) — nơi tác giả phát biểu quan điểm cá nhân.
- **Không** dùng "chúng tôi" hay "nhóm tác giả" vì đây là luận văn cá nhân.

**Ví dụ:**
> *"Nhận thấy vấn đề trên, tôi quyết định thực hiện đề tài này..."* (Chương 1)
> *"...tác giả đã tìm được một vài ứng dụng và kỹ thuật có tính ứng dụng..."* (Chương 2)

---

## 2. Câu mở đầu chương & section

### Mở đầu chương
Luôn có **1 câu dẫn nhập** tóm tắt nội dung chương, đặt ngay sau `\chapter{}`.

Template thông dụng:
```
Trong chương này, tác giả sẽ [động từ] [nội dung chương].
```

Biến thể khác (dùng cho chương kết luận):
```
Nội dung chương này sẽ khái quát lại [nội dung], nhận xét và định hướng tương lai.
```

**Ví dụ từ file mẫu:**
> *"Trong chương này, tác giả sẽ giới thiệu tổng quan về nội dung của đề tài cùng với mục tiêu đề ra trong quá trình thực hiện đề tài."*
> *"Trong chương này, tác giả sẽ trình bày các kiến thức nền tảng cần thiết để hướng đến xây dựng [tên hệ thống]."*
> *"Nội dung chương này sẽ khái quát lại những điều đã làm được, nhận xét và định hướng tương lai."*

### Mở đầu section
Đi thẳng vào nội dung, **không** cần câu dẫn thêm. Bắt đầu bằng định nghĩa hoặc ngữ cảnh của khái niệm.

---

## 3. Định nghĩa kỹ thuật

Khi giới thiệu một khái niệm kỹ thuật lần đầu, theo cấu trúc 3 bước:

**Bước 1: Định nghĩa trích dẫn** (block quote nghiêng, tiếng Anh, có `\cite{}`):
```latex
\emph{"[Định nghĩa nguyên văn tiếng Anh]" \cite{key}.}
```

**Bước 2: Giải thích tiếng Việt** (1–2 câu, diễn giải định nghĩa trên):
> *"Các vector ánh xạ này có thể học được mối quan hệ ngữ nghĩa giữa các từ..."*

**Bước 3: Mở rộng** (đặc điểm, ứng dụng, ví dụ thực tế):
Dùng `\begin{itemize}` với từ khóa **in đậm**.

**Lưu ý:** `\emph{}` cũng được dùng để highlight câu ví dụ tiếng Việt trong phần giải thích:
```latex
\emph{"Chương trình đào tạo thạc sĩ công nhận chứng chỉ bồi dưỡng sau đại học..."}
```

---

## 4. Thuật ngữ song ngữ

Lần **đầu tiên** xuất hiện: viết tiếng Việt trước, tiếng Anh trong ngoặc đơn, viết tắt in hoa.

```
[Tiếng Việt] ([Tiếng Anh] - [Viết tắt])
```

**Ví dụ:**
> *"Xử lý ngôn ngữ tự nhiên (Natural Language Processing - NLP)"*
> *"Truy xuất thông tin (Information Retrieval - IR)"*
> *"học sâu (deep learning)"* — không viết tắt nếu không có viết tắt chuẩn

Từ lần thứ hai trở đi: chỉ dùng viết tắt hoặc tên tiếng Anh.

---

## 5. Danh sách (Itemize / Enumerate)

### Liệt kê đặc điểm — dùng `itemize`
- Từ khóa đầu mỗi item **in đậm** (`\textbf{}`), theo sau là dấu hai chấm.
- Sau phần in đậm: giải thích 1–4 câu.
- Cho phép lồng tối đa **3 cấp** (`itemize > itemize > itemize`).

```latex
\begin{itemize}
    \item \textbf{Tên đặc điểm}: Giải thích chi tiết...
    \begin{itemize}
        \item Chi tiết cấp 2
    \end{itemize}
\end{itemize}
```

### Liệt kê có thứ tự / bước thuật toán — dùng `enumerate`
- Dùng khi liệt kê các bước thuật toán, quy trình, hoặc nội dung có thứ tự bắt buộc.
- Cho phép lồng `itemize` bên trong để giải thích chi tiết từng bước.

### Sau mỗi danh sách
- Với **danh sách đặc điểm/mô tả**: thêm 1–2 câu văn xuôi tổng kết ý nghĩa.
- Với **danh sách bước quy trình hoặc phần kết quả**: có thể kết thúc bằng danh sách, không bắt buộc phải có câu tổng kết.

---

## 6. Header inline (không tạo subsection mới)

Khi muốn thêm tiêu đề nhỏ **trong thân section** mà không tạo subsection, dùng hai cách:

### Cách 1: `\textbf{}` đứng đầu dòng (cho tên bước / nhóm)
```latex
\textbf{Bước 1: Tên bước}

[Nội dung bước 1...]

\textbf{Bước 2: Tên bước}
```

Dùng khi trình bày các bước thuật toán có tên rõ ràng (không dùng enumerate).

### Cách 2: `\noindent\textbf{}` với `\bigskip` (cho tiêu đề giữa đoạn)
```latex
\bigskip

\noindent\textbf{Tên tiêu đề:}

[Nội dung...]
```

Dùng khi muốn phân tách các khối nội dung lớn trong cùng một section (ví dụ: chia "Quy trình tính" và "Công thức toán học" trong cùng một section về metric).

---

## 7. Công thức toán học

### Công thức đơn, có đánh số: dùng `\begin{equation}`
```latex
\begin{equation}
    Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
\end{equation}
Trong đó:
\begin{itemize}
    \item $A_{ij}$: Trọng số cạnh giữa node $i$ và $j$,
    \item $k_i$: Tổng trọng số cạnh liên quan đến node $i$.
\end{itemize}
```

### Nhiều công thức liên quan, không đánh số: dùng `\[...\]`
```latex
\[
\text{Precision} = \frac{1}{|C|} \sum_{c \in C} \max_{r \in R} \text{cosine\_similarity}(c, r)
\]

\[
\text{Recall} = \frac{1}{|R|} \sum_{r \in R} \max_{c \in C} \text{cosine\_similarity}(r, c)
\]
```

Dùng khi trình bày bộ công thức (Precision, Recall, F1) — mỗi công thức trên một dòng riêng.

Sau bộ công thức: có 1–2 câu giải thích **ý nghĩa thực tế** trong bối cảnh nghiên cứu.

---

## 8. Hình ảnh & Bảng

### Hình ảnh
- Đặt hình **sau** đoạn văn có `\ref{}` tham chiếu đến nó — text trước, hình theo sau.
- Caption mô tả nội dung hình, **không** chỉ đặt tên.
- Dùng `[H]` (package `float`) để ép hình nằm **đúng vị trí** trong source, không bị LaTeX float sang trang khác.
- **Không** dùng `[!h]` hay `[h]` khi cần hình đứng đúng chỗ — hai specifier này chỉ là gợi ý, LaTeX có thể bỏ qua và đẩy hình sang trang kế.

```latex
% Preamble (đã có trong thesis.tex):
\usepackage{float}
\usepackage[bottom]{footmisc}   % giữ footnote luôn ở biên dưới trang

\begin{figure}[H]               % H = ép đúng vị trí, không float
    \centering
    \includegraphics[width=0.8\linewidth]{Images/ten_hinh.png}
    \caption{Mô tả nội dung hình}
    \label{fig:ten_nhan}
\end{figure}
```

> **Lý do cần `[bottom]{footmisc}`:** Khi hình bị ép ở giữa trang và còn khoảng trắng thừa bên dưới, LaTeX mặc định đẩy footnote sát văn bản thay vì giữ ở cuối trang. Package `footmisc` với option `bottom` sửa hành vi này.

### Bảng
- Caption **trên** bảng (`\caption{}` và `\label{}` trước `\begin{tabular}`).
- Dùng `|l|c|c|` với `\hline` (kiểu truyền thống phổ biến trong luận văn này).
- Sau bảng kết quả: có đoạn văn xuôi phân tích số liệu (có thể dùng itemize hoặc `\paragraph{Nhận xét:}`).

```latex
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

---

## 9. Code và ví dụ lệnh

Ba môi trường tùy theo ngữ cảnh:

### `\begin{minted}{language}` — code có syntax highlight
Dùng cho JSON, Python, hoặc code phức tạp cần highlight.
```latex
\begin{minted}{json}
{
    "key": "value"
}
\end{minted}
```

### `\begin{lstlisting}[language=X]` — code ngôn ngữ đặc thù
Dùng cho các ngôn ngữ query (Cypher, SQL, ...).
```latex
\begin{lstlisting}[language=cypher]
MATCH (n:Organization) RETURN n LIMIT 25
\end{lstlisting}
```

### `\begin{verbatim}` — lệnh đơn giản, không cần highlight
Dùng cho lệnh ngắn, câu query đơn giản.
```latex
\begin{verbatim}
MATCH (n:Organization) RETURN n LIMIT 25
\end{verbatim}
```

### Ví dụ kèm code — pattern thường gặp
```latex
\paragraph{Ví dụ:} Mô tả ngắn về ví dụ.
\begin{verbatim}
[Lệnh hoặc code]
\end{verbatim}
\textbf{Giải thích:}
\begin{itemize}
    \item \texttt{phần\_code}: Giải thích ý nghĩa.
\end{itemize}
```

Dùng `\texttt{}` để highlight tên lệnh/biến inline trong văn xuôi.

---

## 9b. Viết về hệ thống/pipeline — không nhắc tên code

Khi mô tả thiết kế hoặc hoạt động của pipeline trong luận văn, **không nhắc đến tên hàm, tên biến, tên tham số, hay đường dẫn file** vì người đọc không có source code và những chi tiết đó không truyền tải ý nghĩa học thuật.

### Nguyên tắc

- **Mô tả hành vi, không mô tả cách gọi.** Thay vì "hàm `_call_with_retry()` gọi `client.generate()`", viết "lời gọi API được bảo vệ bởi cơ chế thử lại tự động".
- **Dùng từ ngữ khái niệm thay cho tên code.** Thay vì "thuộc tính `supports_vision`", viết "khả năng xử lý ảnh của mô hình".
- **Đường dẫn file chỉ dùng trong hình minh họa hoặc phụ lục**, không lồng vào văn xuôi mô tả quy trình.
- **Không nhắc tên lớp nội bộ** (class name) trong văn xuôi. Thay bằng tên chức năng: "Pipeline A", "Pipeline B", "engine OCR" thay vì `VLMDirectPipeline`, `OCRLLMPipeline`, `EasyOCREngine`. Tên class chỉ xuất hiện trong bảng so sánh kỹ thuật ở phụ lục, không lồng vào thân văn bản.

### Bảng ví dụ đối chiếu

| Sai — nhắc tên code | Đúng — mô tả hành vi |
|---|---|
| `Hàm _parse_json_response() tước markdown fence` | `Phản hồi được xử lý để loại bỏ phần định dạng bao bọc` |
| `Thuộc tính supports_vision kiểm tra...` | `Pipeline kiểm tra xem mô hình có khả năng xử lý ảnh hay không` |
| `_pace() duy trì khoảng cách tối thiểu` | `Pipeline chủ động đợi một khoảng thời gian tối thiểu giữa các lần gọi` |
| `ocr_chars lưu vào trường meta` | `Số ký tự trích xuất được lưu vào metadata` |
| `render_prompt() điền placeholder` | `Hệ thống điền field schema vào template prompt` |
| `config/prompts/vlm_direct.md chứa...` | `Template prompt được lưu trong file cấu hình riêng` |

### Ngoại lệ được phép

- Tên thư viện/công cụ bên ngoài: `EasyOCR`, `Pillow`, `Azure Document Intelligence` — đây là tên sản phẩm, không phải tên code nội bộ.
- Tên model ID trong **bảng** so sánh: `gpt-4o`, `Phi-4-multimodal-instruct` — đặt trong cột bảng, không lồng vào văn xuôi.
- Hằng số cấu hình có giá trị rõ nghĩa: `temperature=0` — vì đây là tham số thực nghiệm quan trọng, không phải tên biến nội bộ.

---

## 10. Trích dẫn tài liệu

- Dùng `\cite{key}` **ngay sau** khái niệm hoặc câu phát biểu cần dẫn nguồn.
- Không để một đoạn dài không có citation khi nội dung lấy từ tài liệu.
- Với định nghĩa trích nguyên văn: citation đặt **trong** block `\emph{}`.
- Với công cụ/thư viện (không có paper): dùng footnote để ghi URL nguồn.

### Quy tắc footnote

**Format chuẩn: `Tên: \url{...}` (luôn có dấu hai chấm sau tên)**

```latex
% Footnote inline — dùng khi không nằm trong list/enumerate
EasyOCR\footnote{EasyOCR: \url{https://github.com/JaidedAI/EasyOCR}} là thư viện...

% Footnote tách đôi — bắt buộc khi nằm trong \begin{itemize} hoặc \begin{enumerate}
\item \textbf{\texttt{GeminiClient}}\footnotemark: Gọi API Google AI Studio...
\footnotetext{google-generativeai: \url{https://github.com/google-gemini/generative-ai-python}}
```

**Quy tắc URL:**
- Thư viện Python: dùng link PyPI (`https://pypi.org/project/...`) hoặc GitHub repo
- Dịch vụ/API: dùng link tài liệu chính thức của nhà cung cấp
- Thư viện có docs riêng: ưu tiên link readthedocs (`https://xxx.readthedocs.io`)
- **Nhất quán**: cùng một thư viện phải dùng cùng một URL trong toàn luận văn

**Quy tắc lặp footnote:**
- Chỉ đặt footnote tại **lần xuất hiện đầu tiên** của mỗi thư viện/công cụ trong mỗi chương
- Nếu cùng thư viện xuất hiện ở hai chương khác nhau, có thể lặp footnote

**Trường hợp đặc biệt — URL-only (không cần tên trước URL):**
- Tiêu đề section: `\section[...]{...\protect\footnote{\url{...}}}` — tên đã có trong tiêu đề
- Dataset với tên đã in đậm ngay trước: `\textbf{Tên dataset}\footnote{\url{...}}` — tên đã rõ

```latex
% Trích dẫn paper
Neo4j\cite{neo4j-official} là một cơ sở dữ liệu đồ thị...

% Thư viện/tool — inline
Pillow\footnote{Pillow: \url{https://pillow.readthedocs.io}} được dùng để...

% Thư viện/tool — trong list
\item \textbf{Tên}\footnotemark: Mô tả...
\footnotetext{Tên thư viện: \url{https://...}}
```

- Bibliography style: `\bibliographystyle{ieeetr}` (IEEE format).

---

## 11. Cross-references nội bộ

Dùng `\hyperref[label]{text}` để tham chiếu đến section/figure/table khác trong luận văn:

```latex
% Tham chiếu section
...được trình bày ở \hyperref[sec:ten_section]{Mục X.Y}.
...sử dụng thuật toán \hyperref[sec:LeidenAlgorithm]{Leiden}.

% Tham chiếu figure/table
...như minh họa ở Hình~\ref{fig:ten_nhan}.
```

**Không** viết "như đã nói ở trên" — luôn dùng `\hyperref` hoặc `\ref` thay thế.

---

## 12. Nhận xét & Đánh giá công trình liên quan (Chương 2)

**Không phải mọi công trình đều cần đủ hai phần.** Tùy mức độ phức tạp:

- **Công trình đơn giản** (tool, thư viện): chỉ mô tả, không cần nhận xét riêng.
- **Công trình trung bình** (phương pháp, model): kết thúc bằng `\paragraph{Nhận xét:}`.
- **Công trình phức tạp, trọng tâm** (phương pháp chính so sánh): thêm cả `\subsection*{Nhược điểm}`.

```latex
% Nhận xét — dùng cho hầu hết công trình
\paragraph{Nhận xét:}
[2–4 câu về ưu điểm, phạm vi áp dụng, kết quả nổi bật]

% Nhược điểm — chỉ dùng cho công trình quan trọng, liên quan trực tiếp
\subsection*{Nhược điểm của phương pháp [Tên]}
\begin{enumerate}
    \item \textbf{Tên nhược điểm}:
    \begin{itemize}
        \item Chi tiết 1
        \item Chi tiết 2
    \end{itemize}
\end{enumerate}
```

---

## 13. Độ dài & nhịp câu

| Loại câu | Độ dài khuyến nghị |
|---|---|
| Câu định nghĩa | 20–40 từ |
| Câu giải thích | 25–50 từ |
| Câu nhận xét/kết luận | 15–30 từ |
| Câu mở đầu chương/section | 15–25 từ |

- **Không** dùng câu quá ngắn (< 10 từ) trừ câu nhấn mạnh.
- **Không** dùng câu quá dài (> 60 từ) — tách thành 2 câu.
- Đảm bảo mỗi đoạn văn có **ít nhất 3 câu** và **tối đa 6–7 câu**.

---

## 14. Tông văn phong tổng quát

| Đặc điểm | Mô tả |
|---|---|
| **Khách quan** | Không dùng cảm xúc, không phán xét chủ quan |
| **Học thuật** | Chính xác, có dẫn chứng, không mơ hồ |
| **Rõ ràng** | Mỗi câu một ý, không nhồi nhét |
| **Nhất quán** | Cùng một thuật ngữ dùng xuyên suốt |
| **Trung lập** | Khi so sánh: nêu ưu nhược điểm, không thiên vị |

### Các cụm từ nên dùng
- *"Phương pháp này cho phép..."*
- *"Kết quả thực nghiệm cho thấy..."*
- *"Tác giả đề xuất..."* / *"Tác giả sử dụng..."*
- *"Nhằm giải quyết vấn đề..."*
- *"Điều này cho phép mô hình..."*
- *"Có thể nhận thấy rằng..."*

### Các cụm từ nên tránh
- ~~"Rất tốt"~~ → dùng "đạt hiệu quả cao" hoặc nêu con số cụ thể
- ~~"Như đã nói ở trên"~~ → dùng `\hyperref[sec:label]{Mục X.Y}`
- ~~"Hiển nhiên là..."~~ → không dùng, chứng minh thay vì khẳng định
- ~~"Chúng ta thấy rằng..."~~ → dùng "Có thể nhận thấy rằng..."

### Dấu câu: không dùng dấu gạch ngang dài (—)

Không dùng dấu "—" (em dash) trong văn bản luận văn. Thay bằng:

| Mục đích | Thay bằng |
|---|---|
| Giải thích bổ sung | Dấu phẩy hoặc dấu ngoặc đơn `(...)` |
| Liệt kê tên con/loại | Dấu hai chấm `:` |
| Nối mệnh đề tương phản | Dùng từ nối: "trong khi đó", "tuy nhiên", "ngược lại" |
| Tiêu đề phụ inline | Dấu hai chấm `:` |

**Ví dụ:**
- Sai: *"Pipeline A — VLM Direct: đưa ảnh vào mô hình..."*
- Đúng: *"Pipeline A (VLM Direct): đưa ảnh vào mô hình..."*

---

## 15. Cấu trúc tổng quan mỗi section (Chương 3 — Cơ sở lý thuyết)

```
[Tên Section]
│
├── Định nghĩa (block quote \emph{} + \cite{})
├── Giải thích tiếng Việt (2–3 câu)
├── Đặc điểm chính (itemize với \textbf{})
├── Ví dụ thực tế / Hình minh họa
└── Liên hệ với đề tài (1–2 câu kết nối sang nghiên cứu hiện tại)
```

---

## 16. Cấu trúc tổng quan mỗi công trình (Chương 2 — Công trình liên quan)

```
[Tên Section — Tên công trình]
│
├── Giới thiệu ngắn (1 câu: tên, tác giả/tổ chức, mục đích)
├── Phương pháp / Kiến trúc (itemize hoặc subsection)
├── Hình minh họa (nếu có)
├── Kết quả / Đánh giá (bảng số liệu nếu có)
├── \paragraph{Nhận xét:} (ưu điểm, đóng góp) — hầu hết công trình
└── \subsection*{Nhược điểm} (enumerate) — chỉ công trình quan trọng
```

---

## 17. Tiêu đề section dài — tự động xuống dòng

Preamble của `thesis.tex` đã cấu hình `titlesec` để tất cả `\section` và `\subsection` tự wrap (không overflow):

```latex
\usepackage{titlesec}
\titleformat*{\section}{\Large\bfseries\raggedright}
\titleformat*{\subsection}{\large\bfseries\raggedright}
\setlength{\emergencystretch}{3em}
```

**Quy tắc khi viết tiêu đề section:**
- **KHÔNG** thêm `\\` thủ công vào tiêu đề — LaTeX sẽ tự xuống dòng.
- **KHÔNG** rút ngắn tiêu đề để tránh overflow — giữ nguyên tên đầy đủ.
- Nếu tiêu đề rất dài và muốn TOC/header gọn hơn, dùng cú pháp `\section[tên ngắn]{Tên đầy đủ dài}`.
- `\cite{}` **không được đặt trong `\section{}`** — sẽ ra `[?]`. Đặt cite trong phần thân văn bản thay vì trong tiêu đề.
- Với nguồn không có paper (tool, URL), dùng `\protect\footnote{\url{...}}` đặt **trong** `\section{}` — trường hợp này URL-only là chấp nhận được vì tên đã có trong tiêu đề.

**Ví dụ đúng:**
```latex
\section[Multi-Modal Vision vs. Text-Based Parsing]{Multi-Modal Vision vs. Text-Based Parsing: Benchmarking LLM Strategies for Invoice Processing}
```

---

## 18. Cấu trúc Chương 5 — Kết luận

```
\chapter{Kết luận}
[1 câu mở đầu chương]

\section{Nhận xét và tổng kết}
[1 đoạn văn xuôi tổng kết những gì đã làm được + kết quả đạt được]

\section{Hạn chế của nghiên cứu}
[itemize liệt kê các hạn chế / thách thức còn tồn tại]

\section{Hướng phát triển trong tương lai}
[1–2 câu dẫn nhập về tiềm năng cải thiện]
[itemize liệt kê hướng phát triển]
[1–2 câu kết thúc khẳng định đóng góp của nghiên cứu]
```
