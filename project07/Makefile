PYTHON_SCRIPT = VMTranslator.py
RUN_FILE_NAME = VMtranslator

$(RUN_FILE_NAME): $(PYTHON_SCRIPT)
	cp $(PYTHON_SCRIPT) $(RUN_FILE_NAME)
	chmod +x $(RUN_FILE_NAME)

clean:
	rm -f $(RUN_FILE_NAME)
.PHONY: clean