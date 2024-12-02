FROM locustio/locust

COPY locustfile.py /mnt/locust/

CMD ["-f", "/mnt/locust/locustfile.py", "--host", "https://ase.localhost"] 