KTcloud 에서 openapi 서비스를 제공하고 있습니다.

KTcloud 에서는 크게 G 와 D 플랫폼이 존재하며 이에 따라 openapi 사용방법이 다릅니다.

고객사 환경이 D에 있기에 D 플랫폼에서 사용가능한 openapi 를 사용하였기에 G 플랫폼에서는 해당 코드는 사용이 불가능 합니다.

baseurl 에서 플랫폼 D 에 있는 존을 구분할 수 있는데

예로 오픈스택에 falvor 정보를 조회할 수 있는 openapi 주소 인 "https://api.ucloudbiz.olleh.com/d1/server/flavors" 를 본다면

아래의 내용에서 처럼 "d1" 은 M1 존을 의미하며 자신이 사용중인 각 존에 맞춰 사용하면 됩니다.

DX-M1	d1 (https://api.ucloudbiz.olleh.com/d1/server/flavors)

DX-Central	d2 (https://api.ucloudbiz.olleh.com/d2/server/flavors)

DX-DCN-CJ	d3 (https://api.ucloudbiz.olleh.com/d3/server/flavors)

DX-G gd1 (공공기관) (https://api.ucloudbiz.olleh.com/gd1/server/flavors)

작성된 코드 중 일부는 KTcloud 에서 제공하는 openapi 메뉴얼에 존재하지 않았지만 여러 테스트와 추측을 통해서 발견한 내용입니다.

KTcloud 에도 "serverless code run" 이라는 무료 상품이 있지만 공공기관에서는 해당 상품이 제공되지 않기에 NCP의 cloud function 기능을 위해 작성한 코드 입니다.

실행 파라미터 예시
python 에서 직접 실행하려면 
main({"nasname": "productnas","user":"root@root.com","pwd":"rootpwd"})

NCP cloud function 에서 실행을 위해 사용하려면 
{"nasname": "productnas","user":"root@root.com","pwd":"rootpwd"}

현재 본인의 업무를 위해 작성한 로직은 다음과 같습니다.

1. cloud function 을 통해 일주일에 1회만 실행된다
2. 특정 NAS에 snapshot 이 2개 미만일때에는 NAS snapshot 을 생성한다
3. 2회(2주)를 통해 snapshot 이 2개 초과하게 되면 생성된지 2주가 지난 NAS snapshot 을 삭제한다.

2024년 6월 1일 작성
