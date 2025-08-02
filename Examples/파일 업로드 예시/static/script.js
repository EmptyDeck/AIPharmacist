document.getElementById('csvForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    if (!file) return alert("CSV 파일을 선택하세요.");

    const formData = new FormData();
    formData.append("file", file);

    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "분석 중...";

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            resultDiv.innerHTML = `<div style="color:red;">${data.error}</div>`;
            return;
        }

        let tableHTML = "<table><tr><th>이름</th><th>나이</th></tr>";
        data.preview.forEach(row => {
            tableHTML += `<tr><td>${row['이름']}</td><td>${row['나이']}</td></tr>`;
        });
        tableHTML += "</table>";

        resultDiv.innerHTML = `
            <h4>CSV 미리보기 (상위 5개)</h4>
            ${tableHTML}
            <p><b>나이 평균값:</b> ${data.avg_age}</p>
        `;

    } catch (err) {
        resultDiv.innerHTML = `<div style="color:red;">오류 발생: ${err}</div>`;
    }
});
