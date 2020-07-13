FROM python:3.8.3-buster
MAINTAINER mkrueger@rstms.net
RUN pip install -U txtrader-monitor
CMD txtrader_monitor
