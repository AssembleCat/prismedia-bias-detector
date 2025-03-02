FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    g++ \
    curl \
    wget \
    bash \
    make \
    automake \
    autoconf \
    libtool \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install mecab
RUN wget -O mecab-0.996.tar.gz 'https://drive.google.com/uc?id=0B4y35FiV1wh7cENtOXlicTFaRUE&export=download' \
    && tar -zxf mecab-0.996.tar.gz \
    && cd mecab-0.996 \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
    && cd .. \
    && rm -rf mecab-0.996*

# Install mecab-ko-dic
RUN wget -O mecab-ko-dic-2.1.1-20180720.tar.gz 'https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz' \
    && tar -zxf mecab-ko-dic-2.1.1-20180720.tar.gz \
    && cd mecab-ko-dic-2.1.1-20180720 \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf mecab-ko-dic-2.1.1-20180720*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create output directory
RUN mkdir -p output

# Run the application
CMD ["python", "main.py"]
