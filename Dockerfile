FROM python:3-alpine

 # Necessary for build hooks
ARG BUILD_DATE
ARG VCS_REF

# # Good docker practice, plus we get microbadger badges
LABEL org.label-schema.build-date=$BUILD_DATE \
       org.label-schema.vcs-url="https://github.com/rubasace/radarr-folder-organizer.git" \
       org.label-schema.vcs-ref=$VCS_REF \
       org.label-schema.schema-version="2.2-r1"

# Copy the script and requirements. Note that we don't copy Config.txt - this needs to be bind-mounted
COPY FolderOrganizer.py /
COPY requirements.txt /
COPY entrypoint.sh /

RUN chmod 755 /entrypoint.sh && pip install -r requirements.txt

VOLUME "/logs"

CMD [ "/entrypoint.sh" ]

