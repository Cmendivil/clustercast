FROM public.ecr.aws/lambda/python:3.13

# Install any dependencies here
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the function code into the container
COPY main.py .
COPY batch.py .
CMD ["main.lambda_handler"]
