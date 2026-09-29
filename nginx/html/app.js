// 프로젝트 소개 내용을 Flask API에서 불러와 화면에 표시합니다.
async function loadProject() {
  const response = await fetch('/api/project');

  if (!response.ok) {
    throw new Error('프로젝트 소개 API 연결을 확인하세요.');
  }

  const data = await response.json();

  document.querySelector('#project-title').textContent = data.title;
  document.querySelector('#project-summary').textContent = data.summary;
  document.querySelector('#project-features').textContent = data.features;
  document.querySelector('#project-technology').textContent = data.technology;
  document.querySelector('#project-team').textContent = data.team;
}


// 조회수 API 처리
async function updateViews(method) {
  const response = await fetch('/api/views', {
    method: method
  });

  if (!response.ok) {
    throw new Error('조회수 API 연결을 확인하세요.');
  }

  const data = await response.json();

  document.querySelector('#view-count').textContent = data.views;
}


const message = document.querySelector('#message');


// 페이지 로드 시 프로젝트 소개 불러오기
loadProject().catch(error => {
  message.textContent = error.message;
});


// 페이지 로드 시 조회수 1 증가
updateViews('POST').catch(error => {
  message.textContent = error.message;
});


// 조회수 다시 확인 버튼
document
  .querySelector('#refresh-views')
  .addEventListener('click', () => {

    updateViews('GET').catch(error => {
      message.textContent = error.message;
    });

  });


// 소개 내용 다운로드 버튼
document
  .querySelector('#download-button')
  .addEventListener('click', async event => {

    const button = event.currentTarget;

    button.disabled = true;

    try {

      const ids = {
        title: 'project-title',
        summary: 'project-summary',
        features: 'project-features',
        technology: 'project-technology',
        team: 'project-team'
      };


      const data = Object.fromEntries(

        Object.entries(ids).map(([key, id]) => [

          key,

          document
            .getElementById(id)
            .innerText
            .trim()

        ])

      );


      const response = await fetch('/api/download', {

        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify(data)

      });


      if (!response.ok) {

        const errorData = await response.json();

        throw new Error(
          errorData.error || '다운로드 실패'
        );

      }


      const blob = await response.blob();

      const url = URL.createObjectURL(blob);


      const link = document.createElement('a');

      link.href = url;

      link.download = 'project-intro.md';

      document.body.appendChild(link);

      link.click();

      link.remove();


      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 1000);


      message.textContent =
        '다운로드한 파일과 화면의 소개 내용을 비교하세요.';


    } catch (error) {

      message.textContent = error.message;

    } finally {

      button.disabled = false;

    }

  });