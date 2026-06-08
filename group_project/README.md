# Group Project — Search Engine / RAG Chatbot

Folder này sẽ chứa sản phẩm group project cuối cùng của nhóm.

Hiện tại mỗi thành viên sẽ phát triển thử nghiệm group project ở repo/folder riêng. Sau khi cả nhóm hoàn thành, nhóm sẽ review và chọn phiên bản tốt nhất để đưa vào folder này.

---

## 1. Thành viên

| Thành viên | Phần cá nhân | Repo/Folder project thử nghiệm | Trạng thái |
|---|---|---|---|
| Nhi | `individual/Nhi/` | TBD | Đang phát triển |
| Huy | `individual/Huy/` | TBD | Chờ cập nhật |
| Nghia | `individual/Nghia/` | TBD | Chờ cập nhật |

---

## 2. Định hướng sản phẩm group

Sản phẩm cuối cùng sẽ là web app có:

- Search Engine để tra cứu tài liệu pháp luật và bài báo.
- RAG Chatbot trả lời bằng tiếng Việt, có citation.
- Hiển thị source documents.
- Hỗ trợ follow-up questions hoặc conversation memory.
- Evaluation pipeline với golden dataset tối thiểu 15 câu hỏi.
- A/B testing ít nhất 2 cấu hình retrieval.

Khuyến nghị: xây dựng một web app có cả hai chế độ:

```text
Mode 1: Search Engine
Mode 2: RAG Chatbot
```

---

## 3. Cấu trúc dự kiến sau khi chọn bản cuối

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

## 4. Yêu cầu 1 — Search Engine / RAG Chatbot

### Search Engine

Chế độ Search Engine cần:

- Nhận query từ user.
- Chạy retrieval pipeline.
- Hiển thị danh sách kết quả được xếp hạng.
- Mỗi kết quả có:
  - Source file
  - Type: legal/news
  - Score
  - Snippet/preview
  - Metadata nếu có

### RAG Chatbot

Chế độ RAG Chatbot cần:

- Nhận câu hỏi tự nhiên từ user.
- Retrieve context liên quan.
- Gọi LLM để sinh câu trả lời.
- Trả lời bằng tiếng Việt.
- Có citation dạng `[Document i]`.
- Hiển thị source documents đã dùng.
- Không đoán nếu context không đủ bằng chứng.
- Có thể hỗ trợ follow-up questions bằng conversation memory.

---

## 5. Pipeline đề xuất

```text
User Query
→ Semantic Search
→ BM25 Lexical Search
→ RRF Merge
→ Query-aware Reranking
→ PageIndex / Vectorless Fallback
→ Context Formatting
→ Gemini/OpenAI Generation
→ Answer with Citation
```

---

## 6. Yêu cầu 2 — Evaluation Pipeline

Nhóm cần chọn một framework evaluation, ví dụ:

- DeepEval
- RAGAS
- TruLens

Deliverables bắt buộc:

```text
group_project/evaluation/golden_dataset.json
group_project/evaluation/eval_pipeline.py
group_project/evaluation/ab_test.py
group_project/evaluation/results.md
```

Golden dataset cần tối thiểu 15 cặp Q&A:

```json
{
  "question": "...",
  "expected_answer": "...",
  "expected_context": ["..."],
  "category": "legal/news"
}
```

Metrics cần đánh giá:

- Faithfulness
- Answer Relevance
- Context Recall
- Context Precision

A/B testing cần so sánh ít nhất 2 config, ví dụ:

```text
Config A: Hybrid retrieval + RRF
Config B: BM25-only retrieval
```

---

## 7. Báo cáo evaluation

File `evaluation/results.md` cần có:

```markdown
# Evaluation Results

## Setup

- Dataset:
- Framework:
- Model:
- Retrieval configs:

## Overall Scores

| Config | Faithfulness | Answer Relevance | Context Recall | Context Precision |
|---|---:|---:|---:|---:|
| Config A | ... | ... | ... | ... |
| Config B | ... | ... | ... | ... |

## Worst Performers

| Question | Problem | Proposed Fix |
|---|---|---|
| ... | ... | ... |

## Conclusion

...
```

---

## 8. Phân công công việc dự kiến

| Vai trò | Thành viên | Output |
|---|---|---|
| Data lead | TBD | Chọn data tốt nhất, chuẩn hóa `data/` |
| Retrieval lead | TBD | `src/retrieval_pipeline.py` |
| Generation lead | TBD | `src/generation.py` |
| UI lead | TBD | `app.py` |
| Evaluation lead | TBD | `evaluation/` |
| Documentation lead | TBD | `README.md`, `docs/` |

---

## 9. Cách chạy dự kiến

Sau khi group project cuối cùng được đưa vào folder này:

```bash
cd group_project
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Với Mac/Linux:

```bash
cd group_project
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

---

## 10. Biến môi trường

Tạo file `.env` trong `group_project/` dựa trên `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
PAGEINDEX_API_KEY=your_pageindex_api_key
```

Không commit `.env`.

---

## 11. Checklist group project cuối cùng

```text
[ ] Có app chạy được
[ ] Có Search Engine
[ ] Có RAG Chatbot
[ ] Có citation
[ ] Có hiển thị source documents
[ ] Có evaluation/golden_dataset.json với 15+ câu
[ ] Có eval_pipeline.py
[ ] Có ab_test.py
[ ] Có results.md
[ ] Có README hướng dẫn chạy
[ ] Có phân công công việc
[ ] Có screenshot hoặc demo note
```
