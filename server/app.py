from flask import Flask, jsonify, request
import cv2
import numpy as np
import base64

from .model import get_transcript


app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        img_bytes = request.files['img']
        img_bytes = img_bytes.read()
        img_bytes = base64.b64decode(img_bytes)
        nparr = np.fromstring(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        transcripts = get_transcript(img)

        ret = {}
        if transcripts is None:
            ret['status'] = 'fail'
        else:
            ret['status'] = 'ok'
            ret['num_lines'] = len(transcripts)
            for i in range(len(transcripts)):
                ret[str(i + 1)] = transcripts[i]

        return jsonify(ret)


if __name__ == '__main__':
    app.run()
