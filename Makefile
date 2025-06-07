DIRS = retail-ai 
 
.PHONY: all clean distclean install 
 
all: 
	@for dir in $(DIRS); do \
		$(MAKE) -C $$dir all; \
	done

clean: 
	@for dir in $(DIRS); do \
		$(MAKE) -C $$dir clean; \
	done

distclean: 
	@for dir in $(DIRS); do \
		$(MAKE) -C $$dir distclean; \
	done

install: 
	@for dir in $(DIRS); do \
		$(MAKE) -C $$dir install; \
	done
