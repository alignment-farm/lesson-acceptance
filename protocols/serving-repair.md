# Serving repair before fresh evaluation

The first 27B call returned empty content with finish_reason=length after 4096
completion tokens (232.76 seconds); its reasoning field is preserved but is not
treated as an accepted policy. The next in-flight call was interrupted, with
unknown consumed tokens. Stop this recipe; retry four competence calls with
`chat_template_kwargs: {enable_thinking: false}`, supported by the upstream
[llama.cpp server API](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
This is a request option, not a global service configuration change. Validate
actual nonempty output before selecting a reader. Use distinct `27b-direct` call
names; preserve the failed response. The old competence manifest reports 8B due
to a controller ordering bug; the actual preserved request identifies 27B.
Subsequent timestamped manifests record the effective model and code snapshots.

The session deadline is 45 minutes from the first preserved call timestamp,
1789861615 UTC epoch seconds. Cache reuse now checks complete request equality.
All work remains within 60 calls including one interrupted request, accounted
separately. No final calls have run or guided these repairs.
