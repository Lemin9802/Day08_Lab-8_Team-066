# Individual Work — Nhi

Folder này chứa phần bài cá nhân Task 1–10 của Nhi cho Day08 — RAG Pipeline v2.

---

## 1. Mục đích

Đây là phần bài cá nhân đã hoàn thành của Nhi. Toàn bộ code, dữ liệu raw, dữ liệu chuẩn hóa và index phục vụ pipeline cá nhân được lưu trong folder này để tách biệt với phần của các thành viên khác và phần group project.

---

## 2. Cấu trúc folder

```text
individual/Nhi/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── task1_collect_legal_docs.py
│   ├── task2_crawl_news.py
│   ├── task3_convert_markdown.py
│   ├── task4_chunking_indexing.py
│   ├── task5_semantic_search.py
│   ├── task6_lexical_search.py
│   ├── task7_reranking.py
│   ├── task8_pageindex_vectorless.py
│   ├── task9_retrieval_pipeline.py
│   └── task10_generation.py
└── data/
    ├── landing/
    │   ├── legal/
    │   └── news/
    ├── standardized/
    │   ├── legal/
    │   └── news/
    └── index/
```

---

## 3. Các task cá nhân đã hoàn thành

### Task 1 — Thu thập văn bản pháp luật

- Đã thu thập 3 văn bản pháp luật Việt Nam liên quan đến ma túy và các chất cấm.
- File PDF gốc được lưu tại `individual/Nhi/data/landing/legal/`.

### Task 2 — Crawl bài báo

- Đã crawl 5 bài báo tiếng Việt về nghệ sĩ/người nổi tiếng liên quan đến ma túy.
- Dữ liệu crawl dạng JSON được lưu tại `individual/Nhi/data/landing/news/`.

### Task 3 — Convert sang Markdown

- Đã convert các file PDF pháp luật và JSON bài báo sang Markdown.
- File Markdown chuẩn hóa được lưu tại:
  - `individual/Nhi/data/standardized/legal/`
  - `individual/Nhi/data/standardized/news/`

### Task 4 — Chunking & Indexing

- Chiến lược chunking: `RecursiveCharacterTextSplitter`
- `chunk_size`: `800`
- `chunk_overlap`: `120`
- Embedding: local hashing word/character n-gram embedding
- Vector store: local JSON vector store
- File index được lưu tại `individual/Nhi/data/index/`.

### Task 5 — Semantic Search

- Đã triển khai semantic search bằng cosine similarity trên local embeddings.

### Task 6 — Lexical Search

- Đã triển khai BM25 lexical search bằng thư viện `rank-bm25`.

### Task 7 — Reranking

- Đã triển khai Reciprocal Rank Fusion (RRF).
- Bổ sung lightweight query-aware reranking.

### Task 8 — PageIndex / Vectorless Fallback

- Đã triển khai interface tương thích PageIndex cho vectorless fallback.
- Có local vectorless retrieval fallback dựa trên keyword, section và metadata matching.
- `PAGEINDEX_API_KEY` và `GEMINI_API_KEY` được cấu hình qua file `.env`.

### Task 9 — Retrieval Pipeline

- Đã kết hợp semantic search, BM25 search, RRF reranking, query-aware reranking và PageIndex/local fallback.
- Bổ sung query expansion, intent filtering và source diversification cho các câu hỏi tổng hợp về bài báo/nghệ sĩ.

### Task 10 — Generation with Citation

- Đã triển khai generation bằng Gemini.
- Có reorder context để giảm hiện tượng lost-in-the-middle.
- Context được format bằng nhãn `[Document i]`.
- Câu trả lời bằng tiếng Việt, có citation.
- Nếu context không đủ bằng chứng, hệ thống sẽ không đoán và trả lời không thể xác minh từ nguồn hiện có.

---

## 4. Cách chạy phần cá nhân của Nhi

Từ root repo:

```bash
cd individual/Nhi
```

Cài dependencies nếu chưa có:

```bash
python -m pip install -r requirements.txt
```

Tạo file `.env` local dựa trên `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
PAGEINDEX_API_KEY=your_pageindex_api_key
```

Chạy lần lượt các task:

```bash
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
python -m src.task5_semantic_search
python -m src.task6_lexical_search
python -m src.task7_reranking
python -m src.task8_pageindex_vectorless
python -m src.task9_retrieval_pipeline
python -m src.task10_generation
```

---

## 5. Test nhanh phần đã hoàn thành

Có thể test nhanh pipeline retrieval và generation bằng:

```bash
cd individual/Nhi
python -m src.task9_retrieval_pipeline
python -m src.task10_generation
```

Kỳ vọng:

- Retrieval trả về đúng legal docs cho câu hỏi pháp luật.
- Retrieval trả về đúng news articles cho câu hỏi nghệ sĩ/tin tức.
- Generation trả lời bằng tiếng Việt và có citation dạng `[Document i]`.

---

## 6. Lưu ý

- Không commit file `.env`.
- Không commit `.venv/`.
- Không commit `__pycache__/` hoặc `*.pyc`.
- Folder này chỉ chứa phần cá nhân của Nhi; phần group project cuối cùng sẽ nằm trong `group_project/`.
