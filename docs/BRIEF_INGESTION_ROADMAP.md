# Next reviewed layer

After real prospective events begin accumulating, implement story memory and deduplication as a separate PR. That layer may classify new events as REPEAT, CONFIRM, ACCELERATE, DETERIORATE, CONTRADICT or RESOLVE, but it must never mutate the original frozen event records.
