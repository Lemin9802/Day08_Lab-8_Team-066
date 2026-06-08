# Day08 — RAG Pipeline v2 Group Submission

Đây là repository group dùng để nộp bài Day08 — RAG Pipeline v2.

Repository này được tổ chức theo dạng monorepo để chứa:

1. Phần bài cá nhân của từng thành viên.
2. Phần group project cuối cùng của nhóm.
3. Tài liệu hướng dẫn cấu trúc, phân công và cách chạy.

---

## 1. Cấu trúc repo

```text
Day08_RAG_pipeline_cohort2/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── individual/
│   ├── Nhi/
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── src/
│   │   └── data/
│   │
│   ├── Huy/
│   │   └── README.md
│   │
│   └── Nghia/
│       └── README.md
│
└── group_project/
    ├── README.md
    ├── app.py
    ├── requirements.txt
    ├── .env.example
    ├── src/
    ├── data/
    ├── evaluation/
    ├── docs/
    └── screenshots/
```

---

## 2. Quy ước tổ chức bài cá nhân

Tất cả phần bài cá nhân phải nằm trong folder:

```text
individual/<Tên thành viên>/
```

Ví dụ:

```text
individual/Nhi/
individual/Huy/
individual/Nghia/
```

Không để code cá nhân rải ở root repo như:

```text
src/
data/
```

Root repo chỉ dùng để quản lý cấu trúc chung và tài liệu.

---

## 3. Trạng thái bài cá nhân

| Thành viên | Folder | Trạng thái | Ghi chú |
|---|---|---|---|
| Nhi | `individual/Nhi/` | Đã hoàn thành Task 1–10 | Đã có `src/`, `data/`, `requirements.txt`, `.env.example`, README |
| Huy | `individual/Huy/` | Chờ cập nhật | Copy bài cá nhân vào folder này |
| Nghia | `individual/Nghia/` | Chờ cập nhật | Copy bài cá nhân vào folder này |

---

## 4. Cách thành viên copy bài cá nhân vào repo group

Mỗi thành viên làm bài cá nhân ở repo/folder riêng trước. Sau khi hoàn thành, copy các phần sau vào folder tương ứng:

```text
src/
data/
requirements.txt
.env.example
README.md
```

Ví dụ Huy copy vào:

```text
individual/Huy/
```

Ví dụ Nghia copy vào:

```text
individual/Nghia/
```

Chi tiết hướng dẫn nằm trong:

```text
individual/Huy/README.md
individual/Nghia/README.md
```

---

## 5. Quy trình làm việc với Git

Mỗi thành viên nên tạo branch riêng, không push trực tiếp vào `main`.

Ví dụ với Huy:

```bash
git checkout -b add-huy-individual
git add individual/Huy
git commit -m "Add Huy individual submission"
git push origin add-huy-individual
```

Ví dụ với Nghia:

```bash
git checkout -b add-nghia-individual
git add individual/Nghia
git commit -m "Add Nghia individual submission"
git push origin add-nghia-individual
```

Sau đó tạo Pull Request vào `main`.

---

## 6. Group Project

Folder group project nằm tại:

```text
group_project/
```

Hiện tại nhóm đang phát triển thử nghiệm group project ở các repo/folder riêng. Sau khi 3 thành viên hoàn thành bản thử nghiệm, nhóm sẽ review và chọn phiên bản tốt nhất để đưa vào `group_project/`.

Sản phẩm group cuối cùng dự kiến là web app có:

- Search Engine để tra cứu tài liệu pháp luật và bài báo.
- RAG Chatbot trả lời bằng tiếng Việt, có citation.
- Hiển thị source documents.
- Hỗ trợ follow-up questions hoặc conversation memory.
- Evaluation pipeline với golden dataset tối thiểu 15 câu hỏi.
- A/B testing ít nhất 2 cấu hình retrieval.

---

## 7. Cấu trúc dự kiến của `group_project/`

Sau khi chọn bản cuối, folder `group_project/` nên có cấu trúc:

```text
group_project/
├── README.md
├── app.py
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── retrieval_pipeline.py
│   ├── generation.py
│   ├── memory.py
│   └── utils.py
├── data/
│   ├── landing/
│   ├── standardized/
│   └── index/
├── evaluation/
│   ├── golden_dataset.json
│   ├── eval_pipeline.py
│   ├── ab_test.py
│   └── results.md
├── docs/
│   ├── architecture.md
│   └── team_contribution.md
└── screenshots/
    └── demo.png
```

---

## 8. Phân công công việc group project dự kiến

| Vai trò | Thành viên | Output |
|---|---|---|
| Data lead | TBD | Chọn data tốt nhất, chuẩn hóa `data/` |
| Retrieval lead | TBD | `group_project/src/retrieval_pipeline.py` |
| Generation lead | TBD | `group_project/src/generation.py` |
| UI lead | TBD | `group_project/app.py` |
| Evaluation lead | TBD | `group_project/evaluation/` |
| Documentation lead | TBD | `group_project/README.md`, `docs/` |

Có thể gộp vai trò nếu nhóm ít người.

---

## 9. Yêu cầu group project

### 9.1. RAG Chatbot / Search Engine

Sản phẩm cuối cùng nên có:

- Giao diện web bằng Streamlit, Gradio hoặc Chainlit.
- Chế độ Search Engine để tra cứu tài liệu.
- Chế độ RAG Chatbot để hỏi đáp tự nhiên.
- Trả lời có citation.
- Hiển thị source documents đã dùng.
- Có thể hỗ trợ follow-up questions.

### 9.2. Evaluation pipeline

Cần có:

- `group_project/evaluation/golden_dataset.json`
- `group_project/evaluation/eval_pipeline.py`
- `group_project/evaluation/ab_test.py`
- `group_project/evaluation/results.md`

Golden dataset tối thiểu 15 cặp Q&A:

```text
question
expected_answer
expected_context
```

Metrics cần có:

- Faithfulness
- Answer Relevance
- Context Recall
- Context Precision

A/B testing tối thiểu 2 config, ví dụ:

```text
Config A: Hybrid retrieval + RRF reranking
Config B: BM25-only retrieval
```

Báo cáo cần có:

- Bảng điểm.
- Phân tích worst performers.
- Đề xuất cải tiến.

---

## 10. Hướng dẫn chạy phần cá nhân của Nhi

Từ root repo:

```bash
cd individual/Nhi
python -m pip install -r requirements.txt
python -m src.task9_retrieval_pipeline
python -m src.task10_generation
```

Nếu cần chạy đủ toàn bộ task:

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

## 11. Biến môi trường

Không commit file `.env`.

Mỗi thành viên tự tạo `.env` local trong folder cá nhân hoặc trong `group_project/` khi cần chạy code:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
PAGEINDEX_API_KEY=your_pageindex_api_key
```

File `.env.example` chỉ chứa tên biến, không chứa key thật.

---

## 12. Những file không được commit

Không commit:

```text
.env
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
```

Nếu lỡ thấy các file này trong `git status`, cần xóa hoặc đảm bảo `.gitignore` đã ignore.

---

## 13. Checklist trước khi nộp cuối cùng

```text
[ ] individual/Nhi đã có đầy đủ bài cá nhân
[ ] individual/Huy đã có đầy đủ bài cá nhân
[ ] individual/Nghia đã có đầy đủ bài cá nhân
[ ] group_project đã có app cuối cùng
[ ] group_project có README hướng dẫn chạy
[ ] group_project có evaluation/golden_dataset.json với 15+ câu
[ ] group_project có eval_pipeline.py
[ ] group_project có ab_test.py
[ ] group_project có results.md
[ ] README root mô tả đúng cấu trúc repo
[ ] Không có .env, .venv, __pycache__, *.pyc trong git
```
