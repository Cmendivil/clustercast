FROM public.ecr.aws/lambda/python:3.8

# Install any dependencies here
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the function code into the container
COPY app.py .
COPY batch.py .
CMD ["main.lambda_handler"]
