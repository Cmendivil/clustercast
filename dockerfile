FROM public.ecr.aws/lambda/python:3.13

ENV TMPDIR=/tmp
ENV XDG_CACHE_HOME=/tmp

# Install any dependencies here
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the function code into the container
COPY main.py .
COPY batch.py .
CMD ["main.lambda_handler"]
