# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `p95(latency_ms)` thuộc primary SLO `fast_successful_requests`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng bị chậm khi chờ phản hồi câu trả lời từ chatbot AI
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở panel `Latency percentiles and TTFT` trên Dashboard để xác nhận P95/P99 vượt ngưỡng 3000ms và xác định mốc thời gian bắt đầu tăng.
  2. **Logs:** Vào `data/logs.jsonl` lọc các log `response_sent` trong khoảng thời gian bị chậm, tìm request có `latency_ms` cao bất thường và sao chép mã `correlation_id`.
  3. **Traces:** Mở project Langfuse, tìm trace có cùng `correlation_id`, kiểm tra waterfall tree xem span nào (`retrieval` hay `generation`) gây ra độ trễ lớn.
- Mitigation tạm thời: Nếu do retrieval chậm (ví dụ vector store timeout), bật cache hoặc fallback document; nếu do prompt version mới làm tăng token/latency thì rollback prompt về version cũ; nếu do incident kích hoạt, kiểm tra `/incidents/rag_slow/disable`.
- Owner: `student-2A202602619`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `error_rate_pct` và `retrieval_success_rate_pct`
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` hoặc `retrieval_success_rate_pct < 90%` trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi HTTP 500 hoặc câu trả lời không có thông tin chính xác do retrieval thất bại
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Kiểm tra panel `Error rate and retrieval success` trên Dashboard để xem tỷ lệ lỗi `request_failed` và tỷ lệ `tool_success` của retrieval.
  2. **Logs:** Lọc `data/logs.jsonl` tìm các event `request_failed`, xem trường `error_type`, `detail` và lấy `correlation_id` của request lỗi.
  3. **Traces:** Tra cứu `correlation_id` trên Langfuse, quan sát trạng thái lỗi (ERROR level) của span `retrieval` hoặc `generation` để xác định chính xác nguyên nhân (ví dụ: `RuntimeError: Vector store timeout`).
- Mitigation tạm thời: Chuyển hướng traffic sang mô hình/corpus dự phòng, kiểm tra kết nối vector store, hoặc nếu có practice scenario thì gọi `/incidents/tool_fail/disable`.
- Owner: `student-2A202602619`

## Alert 3

- Tên: `DailyCostSpike`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tổng chi phí token `cost_usd` vượt quá guardrail hàng ngày
- Điều kiện và thời gian duy trì: `total_cost_usd > 2.5` USD trong ngày hoặc chi phí tăng vọt theo phút
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp đến người dùng nhưng gây thâm hụt ngân sách vận hành và vi phạm guardrail chi phí
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Kiểm tra panel `Cost over time` và `Input and output tokens` trên Dashboard để xem thời điểm chi phí tăng vọt.
  2. **Logs:** Lọc các log `response_sent` có `cost_usd` hoặc `tokens_out` cao bất thường, lấy `correlation_id`.
  3. **Traces:** Mở trace trên Langfuse, kiểm tra observation `generation` để xem số lượng `output_tokens` và prompt version đang chạy (có bị loop hoặc prompt candidate làm sinh token dài quá mức không).
- Mitigation tạm thời: Áp dụng max_tokens limit chặt chẽ hơn, rollback prompt candidate về prompt baseline có độ dài ngắn gọn, hoặc tắt incident cost spike bằng `/incidents/cost_spike/disable`.
- Owner: `student-2A202602619`
