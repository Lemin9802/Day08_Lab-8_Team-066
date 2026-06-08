# Phân Công Và Đóng Góp Nhóm

## Phân Công Công Việc

| Thành viên | Vai trò | Đóng góp chính | Files liên quan |
|---|---|---|---|
| Thái Thị Yến Nhi | Documentation / Integration Lead | Tổng hợp repo, chuẩn hóa documentation, tích hợp backend generation, đóng góp dữ liệu legal/news, hỗ trợ golden dataset và final cleanup | `README.md`, `docs/`, `src/generation.py`, `evaluation/`, `data/standardized/nhi_*` |
| Trần Quang Huy | UI Lead | Xây dựng Chainlit UI, chatbot UX, source cards, retrieval settings, đóng góp dữ liệu legal/news và câu hỏi evaluation | `chainlit_app.py`, `components/`, `rag/`, `data/standardized/huy_*` |
| Đặng Hữu Nghĩa | Evaluation / Dataset Quality Lead | Đóng góp dữ liệu legal/news, xây dựng và kiểm tra golden questions, validation evaluation, hỗ trợ A/B testing | `data/standardized/nghia_*`, `evaluation/golden_dataset.json`, `evaluation/eval_pipeline.py`, `evaluation/ab_test.py` |

---

## Chính Sách Dataset

Group dataset không copy toàn bộ dữ liệu thô của 3 thành viên. Nhóm dùng cách **curated dataset** để giảm trùng lặp và nhiễu retrieval.

Nguyên tắc lọc dữ liệu:

1. Giữ tài liệu sạch, liên quan trực tiếp đến chủ đề pháp luật ma túy và tin tức nghệ sĩ liên quan đến ma túy.
2. Loại file trùng nội dung, file crawl quá nhiễu hoặc có nội dung không liên quan.
3. Đảm bảo mỗi thành viên đều có nguồn đóng góp trong dataset cuối.
4. Chuẩn hóa dữ liệu về Markdown trong `data/standardized/`.
5. Rebuild một index chung sau khi lọc dữ liệu.

Chi tiết dataset nằm trong:

```text
docs/dataset_inventory.json
```

---

## Output Chính Của Nhóm

| Nhóm output | Mô tả |
|---|---|
| `chainlit_app.py` | Ứng dụng Chainlit chính để demo RAG chatbot. |
| `components/` | Source cards và các thành phần hỗ trợ UI. |
| `rag/` | Adapter kết nối Chainlit với retrieval/generation, memory, prompt và citation handling. |
| `src/build_index.py` | Script build index chung từ curated dataset. |
| `src/retrieval_pipeline.py` | Hybrid retrieval pipeline gồm dense search, BM25, RRF, reranking và fallback. |
| `src/generation.py` | Logic generation có citation và extractive fallback. |
| `data/standardized/` | Curated dataset cuối cùng ở định dạng Markdown. |
| `data/index/` | Index chung đã build từ curated dataset. |
| `evaluation/golden_dataset.json` | Golden dataset gồm 15 câu hỏi. |
| `evaluation/eval_pipeline.py` | Script chạy evaluation pipeline. |
| `evaluation/ab_test.py` | Script chạy A/B testing các retrieval configs. |
| `evaluation/results.md` | Báo cáo evaluation theo metrics. |
| `evaluation/ab_test_results.md` | Báo cáo A/B testing. |
| `docs/architecture.md` | Tài liệu mô tả kiến trúc hệ thống. |
| `docs/dataset_inventory.json` | Inventory mô tả nguồn dữ liệu được giữ/lọc trong curated dataset. |

---

## Tóm Tắt Đóng Góp Theo Thành Viên

### Thái Thị Yến Nhi

- Tổng hợp và chuẩn hóa repo nộp cuối.
- Viết và chỉnh sửa documentation.
- Đóng góp nhóm dữ liệu legal/news.
- Hỗ trợ backend generation và citation handling.
- Hỗ trợ golden dataset, evaluation report và final cleanup.

### Trần Quang Huy

- Xây dựng Chainlit UI cho chatbot.
- Thiết kế chatbot UX và source cards.
- Kết nối UI với retrieval/generation adapters.
- Đóng góp dữ liệu legal/news.
- Đóng góp câu hỏi evaluation cho golden dataset.

### Đặng Hữu Nghĩa

- Đóng góp dữ liệu legal/news.
- Đóng góp golden questions.
- Hỗ trợ kiểm tra chất lượng dataset.
- Hỗ trợ validation evaluation.
- Hỗ trợ A/B testing giữa các retrieval configs.

---

## Ghi Chú

- App demo chính là `chainlit_app.py`.
- Dataset cuối cùng là curated dataset, không phải toàn bộ raw data của từng thành viên.
- Evaluation pipeline dùng 15 câu hỏi đại diện cho cả legal và news.
- A/B testing so sánh `A_hybrid`, `B_lexical`, và `C_vectorless`.
- Gemini generation là tùy chọn; khi API lỗi hoặc hết quota, hệ thống dùng extractive fallback.