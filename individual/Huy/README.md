# Individual Work — Huy

Folder này dành cho phần bài cá nhân Task 1–10 của Huy cho Day08 — RAG Pipeline v2.

Hiện tại folder này là placeholder. Sau khi Huy hoàn thành bài cá nhân trên máy riêng, Huy sẽ copy phần cá nhân vào đây theo cùng cấu trúc với `individual/Nhi/`.

---

## 1. Cấu trúc cần có sau khi copy

```text
individual/Huy/
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

## 2. Những phần Huy cần copy từ repo cá nhân/máy cá nhân vào đây

Huy cần copy các phần sau:

```text
src/
data/
requirements.txt
.env.example
README.md
```

Trong đó:

- `src/`: toàn bộ code Task 1–10.
- `data/landing/`: dữ liệu raw đã thu thập/crawl.
- `data/standardized/`: dữ liệu Markdown sau khi convert.
- `data/index/`: file index sau Task 4 và manifest sau Task 8.
- `requirements.txt`: thư viện cần cài cho phần cá nhân.
- `.env.example`: mẫu biến môi trường, không chứa API key thật.
- `README.md`: mô tả phần cá nhân của Huy.

---

## 3. Cách copy vào repo group trên Windows

Giả sử repo cá nhân của Huy nằm tại:

```text
C:\Users\<USER>\Desktop\Day08_RAG_pipeline_Huy
```

và repo group nằm tại:

```text
C:\Users\<USER>\Desktop\Day08_RAG_pipeline_cohort2
```

Từ terminal trong root repo group, chạy:

```bat
cd "C:\Users\<USER>\Desktop\Day08_RAG_pipeline_cohort2"

xcopy "..\Day08_RAG_pipeline_Huy\src" "individual\Huy\src" /E /I /Y
xcopy "..\Day08_RAG_pipeline_Huy\data" "individual\Huy\data" /E /I /Y
copy "..\Day08_RAG_pipeline_Huy\requirements.txt" "individual\Huy\requirements.txt"
copy "..\Day08_RAG_pipeline_Huy\.env.example" "individual\Huy\.env.example"
copy "..\Day08_RAG_pipeline_Huy\README.md" "individual\Huy\README.md"
```

Nếu folder repo cá nhân có tên khác thì đổi path tương ứng.

---

## 4. Cách copy vào repo group trên Mac/Linux

Giả sử repo cá nhân của Huy nằm tại:

```text
~/Desktop/Day08_RAG_pipeline_Huy
```

và repo group nằm tại:

```text
~/Desktop/Day08_RAG_pipeline_cohort2
```

Từ terminal trong root repo group, chạy:

```bash
cd ~/Desktop/Day08_RAG_pipeline_cohort2

mkdir -p individual/Huy

cp -R ~/Desktop/Day08_RAG_pipeline_Huy/src individual/Huy/
cp -R ~/Desktop/Day08_RAG_pipeline_Huy/data individual/Huy/
cp ~/Desktop/Day08_RAG_pipeline_Huy/requirements.txt individual/Huy/requirements.txt
cp ~/Desktop/Day08_RAG_pipeline_Huy/.env.example individual/Huy/.env.example
cp ~/Desktop/Day08_RAG_pipeline_Huy/README.md individual/Huy/README.md
```

---

## 5. Test sau khi copy

Sau khi copy xong, Huy cần test lại từ đúng folder cá nhân:

```bash
cd individual/Huy
python -m pip install -r requirements.txt
python -m src.task9_retrieval_pipeline
python -m src.task10_generation
```

Nếu Task 10 cần API key, tạo file `.env` local trong `individual/Huy/`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
PAGEINDEX_API_KEY=your_pageindex_api_key
```

File `.env` không được commit.

---

## 6. Tạo branch và mở PR

Từ root repo group:

```bash
git checkout -b add-huy-individual
git add individual/Huy
git commit -m "Add Huy individual submission"
git push origin add-huy-individual
```

Sau đó mở Pull Request vào branch `main` của repo group.

---

## 7. Lưu ý quan trọng

- Không đưa bài cá nhân vào root `src/` hoặc root `data/`.
- Không commit `.env`.
- Không commit `.venv/`.
- Không commit `__pycache__/` hoặc `*.pyc`.
- Chỉ đưa phần cá nhân của Huy vào `individual/Huy/`.
