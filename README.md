<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>차계부 프로그램</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 15px;
            background-color: #f5f5f5;
            -webkit-user-select: none; /* Safari */
            -ms-user-select: none; /* IE 10 and IE 11 */
            user-select: none; /* Standard syntax */
        }
        .container {
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            font-size: 1.5em;
            margin-top: 0;
        }
        .summary {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #e0f7fa;
            border-radius: 5px;
        }
        .summary h3 {
            margin: 0;
            font-size: 1.2em;
        }
        .record-list {
            margin-bottom: 15px;
        }
        .record-list h3 {
            font-size: 1.2em;
            margin-top: 0;
        }
        .record-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
            word-break: break-word; /* 긴 텍스트 줄바꿈 */
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 1em;
        }
        input, button {
            padding: 10px;
            width: 100%;
            box-sizing: border-box;
            font-size: 1em;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        button {
            background-color: #00796b;
            color: white;
            border: none;
            cursor: pointer;
            margin-top: 10px;
            height: 45px; /* 터치 영역 확대 */
        }
        button:hover {
            background-color: #004d40;
        }
        .export-btn {
            background-color: #388e3c;
        }
        .export-btn:hover {
            background-color: #2e7d32;
        }
        .upload-btn {
            background-color: #1976d2;
        }
        .upload-btn:hover {
            background-color: #1565c0;
        }
        /* 모바일 반응형 스타일 */
        @media screen and (max-width: 600px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 10px;
            }
            h1 {
                font-size: 1.3em;
            }
            .summary h3 {
                font-size: 1.1em;
            }
            .record-list h3 {
                font-size: 1.1em;
            }
            .record-item {
                font-size: 0.85em;
                padding: 6px;
            }
            input, button {
                padding: 8px;
                font-size: 0.9em;
            }
            button {
                height: 40px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>차계부 프로그램</h1>
        
        <!-- 요약 정보 -->
        <div class="summary">
            <h3>이번 달 총 비용: <span id="totalCost">0원</span></h3>
        </div>

        <!-- 운행 기록 리스트 -->
        <div class="record-list">
            <h3>최근 운행 기록</h3>
            <div id="records">아직 기록이 없습니다.</div>
            <button class="export-btn" onclick="exportToExcel()">엑셀 파일로 내보내기</button>
            <button class="upload-btn" onclick="document.getElementById('uploadFile').click()">엑셀 파일 업로드</button>
            <input type="file" id="uploadFile" accept=".xlsx, .xls" style="display: none;" onchange="uploadExcel(this)">
        </div>

        <!-- 새로운 운행 추가 폼 -->
        <div class="form-group">
            <h3>새로운 운행 추가</h3>
            <label for="startPoint">출발지</label>
            <input type="text" id="startPoint" placeholder="예: 서울역">
            
            <label for="endPoint">도착지</label>
            <input type="text" id="endPoint" placeholder="예: 수원역">
            
            <label for="tollFee">통행료 (하이패스 자동 입력)</label>
            <input type="number" id="tollFee" placeholder="자동 입력" value="0" readonly>
            
            <label for="fuelCost">주유비 (직접 입력)</label>
            <input type="number" id="fuelCost" placeholder="주유비 입력 (원)" value="0">
            
            <button onclick="addRecord()">운행 기록 저장</button>
        </div>
    </div>

    <!-- SheetJS 라이브러리 CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <script>
        let totalCost = 0;
        let recordList = [];

        function addRecord() {
            const startPoint = document.getElementById('startPoint').value;
            const endPoint = document.getElementById('endPoint').value;
            const tollFee = simulateTollFee(); // 하이패스 모의 데이터
            const fuelCost = parseInt(document.getElementById('fuelCost').value) || 0;

            if (startPoint && endPoint) {
                const total = tollFee + fuelCost;
                totalCost += total;
                document.getElementById('totalCost').textContent = totalCost.toLocaleString() + '원';

                const record = {
                    date: new Date().toLocaleDateString('ko-KR'),
                    route: `${startPoint} → ${endPoint}`,
                    toll: tollFee,
                    fuel: fuelCost,
                    total: total
                };
                recordList.push(record);
                updateRecordList();

                // 입력 필드 초기화
                document.getElementById('startPoint').value = '';
                document.getElementById('endPoint').value = '';
                document.getElementById('fuelCost').value = '0';
                document.getElementById('tollFee').value = tollFee;
            } else {
                alert('출발지와 도착지를 입력해주세요.');
            }
        }

        function simulateTollFee() {
            // 하이패스 연동 대신 랜덤 통행료 모의 데이터 생성
            return Math.floor(Math.random() * 5000) + 1000;
        }

        function simulateTmapHistory(days = 5) {
            // 티맵 API 연동 대신 모의 데이터 생성 (지난 n일간의 이동 경로)
            const history = [];
            const places = ['서울역', '수원역', '인천', '부산', '대전', '광주'];
            for (let i = 0; i < days; i++) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                const start = places[Math.floor(Math.random() * places.length)];
                let end = places[Math.floor(Math.random() * places.length)];
                while (start === end) {
                    end = places[Math.floor(Math.random() * places.length)];
                }
                const tollFee = simulateTollFee();
                const fuelCost = Math.floor(Math.random() * 50000);
                history.push({
                    date: date.toLocaleDateString('ko-KR'),
                    route: `${start} → ${end}`,
                    toll: tollFee,
                    fuel: fuelCost,
                    total: tollFee + fuelCost
                });
            }
            return history;
        }

        function updateRecordList() {
            const recordsDiv = document.getElementById('records');
            recordsDiv.innerHTML = '';
            if (recordList.length === 0) {
                recordsDiv.innerHTML = '아직 기록이 없습니다.';
                return;
            }

            recordList.forEach(record => {
                const recordItem = document.createElement('div');
                recordItem.className = 'record-item';
                recordItem.textContent = `${record.date} | ${record.route} | 통행료: ${record.toll.toLocaleString()}원 | 주유비: ${record.fuel.toLocaleString()}원 | 총 비용: ${record.total.toLocaleString()}원`;
                recordsDiv.appendChild(recordItem);
            });
        }

        function exportToExcel() {
            if (recordList.length === 0) {
                alert('내보낼 운행 기록이 없습니다. 티맵 데이터를 불러오거나 기록을 추가해주세요.');
                return;
            }

            // 엑셀 데이터 준비
            const data = recordList.map(record => ({
                날짜: record.date,
                경로: record.route,
                통행료: record.toll,
                주유비: record.fuel,
                총비용: record.total
            }));

            // 워크시트 생성
            const ws = XLSX.utils.json_to_sheet(data);
            // 워크북 생성
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "차계부_기록");
            // 파일 다운로드
            XLSX.writeFile(wb, "차계부_기록.xlsx");
        }

        function uploadExcel(input) {
            const file = input.files[0];
            if (!file) {
                alert('파일을 선택해주세요.');
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheet = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheet];
                const jsonData = XLSX.utils.sheet_to_json(worksheet);

                // 업로드된 데이터 처리
                if (jsonData.length > 0) {
                    jsonData.forEach(row => {
                        const record = {
                            date: row['날짜'] || new Date().toLocaleDateString('ko-KR'),
                            route: row['경로'] || '알 수 없음',
                            toll: parseInt(row['통행료']) || 0,
                            fuel: parseInt(row['주유비']) || 0,
                            total: (parseInt(row['통행료']) || 0) + (parseInt(row['주유비']) || 0)
                        };
                        recordList.push(record);
                        totalCost += record.total;
                    });
                    document.getElementById('totalCost').textContent = totalCost.toLocaleString() + '원';
                    updateRecordList();
                    alert(`${jsonData.length}개의 기록이 업로드되었습니다.`);
                } else {
                    alert('업로드된 파일에 데이터가 없습니다.');
                }
            };
            reader.readAsArrayBuffer(file);
        }

        // 티맵 API 모의 데이터로 기록 추가 (테스트용)
        window.onload = function() {
            // 페이지 로드 시 티맵 API로 지난 5일간 데이터 가져오기 (모의)
            const tmapHistory = simulateTmapHistory(5);
            tmapHistory.forEach(record => {
                recordList.push(record);
                totalCost += record.total;
            });
            document.getElementById('totalCost').textContent = totalCost.toLocaleString() + '원';
            updateRecordList();
        };
    </script>
</body>
</html>
