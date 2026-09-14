PYTHON_SCRIPT = assembler.py
RUN_FILE_NAME = Assembler

$(RUN_FILE_NAME): $(PYTHON_SCRIPT)
	cp $(PYTHON_SCRIPT) $(RUN_FILE_NAME)
	chmod +x $(RUN_FILE_NAME)

clean:
	rm -f $(RUN_FILE_NAME)
.PHONY: clean