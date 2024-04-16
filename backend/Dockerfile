FROM python:3.7-slim

WORKDIR /usr/src/app/
ADD requirements.txt .
RUN pip3 install -r requirements.txt
COPY backend backend

ENV EMAIL_HOST=""
ENV EMAIL_PORT=""
ENV EMAIL_USER=""
ENV EMAIL_PASSWD=""
ENV PORT=8012
ENV TPC_TOKEN=""
ENV PYTHONPATH=$PYTHONPATH:/usr/src/app/

EXPOSE ${PORT}

CMD python3 backend/api.py -H ${EMAIL_HOST} -p ${EMAIL_PORT} -u "${EMAIL_USER}" -w ${EMAIL_PASSWD} -t ${TPC_TOKEN} -P ${PORT}