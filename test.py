#!/usr/bin/env python3
import json
import urllib.error
import urllib.parse
import urllib.request
from sys import argv
from typing import TextIO

class TestcaseAC:
    API_URL = "https://testcase.ac/api/trpc"
    RESULT_PATH = "./testcase_result.txt"
    RESULT_KOREAN = {
        "AC": "맞았습니다!!",
        "WA": "틀렸습니다",
        "RTE": "런타임 에러",
        "TLE": "시간 초과",
        "MLE": "메모리 초과",
        "OLE": "출력 초과",
        "PE": "출력 형식이 잘못되었습니다"
    }
    
    def __problem_fetcher(self, problem_id: str) -> dict:
        input_param = urllib.parse.quote(json.dumps({"0": {"json": problem_id}}), safe="")
        req = urllib.request.Request(
            f"{self.API_URL}/problem.get?batch=1&input={input_param}",
            headers={"trpc-accept": "application/json", "x-trpc-source": "nextjs-react"}
        )
        try:
            problem =  json.loads(urllib.request.urlopen(req).read())[0]['result']['data']['json']
        except (urllib.error.ContentTooShortError, urllib.error.HTTPError, urllib.error.URLError):
            raise Exception("문제의 정보를 가져오지 못했습니다")

        if not (problem.get('generatorCodes') and problem.get('correctCodes')):
            raise Exception("문제에 제너레이터나 정답 코드가 없습니다")

        return problem
    
    def __stress_tester(self, problem_id: str, payload: dict) -> dict:
        body = json.dumps({"0": {"json": payload, "meta": {"values": {"checkerCodeId": ['undefined']}, "v": 1}}}).encode()
        req = urllib.request.Request(
            f"{self.API_URL}/runner.stress?batch=1",
            data=body,
            headers={
                "content-type": "application/json",
                "origin": "https://testcase.ac",
                "referer": f"https://testcase.ac/problems/{problem_id}",
                "trpc-accept": "application/json",
                "x-trpc-source": "nextjs-react",
            }
        )

        try:
            result = json.loads(urllib.request.urlopen(req).read())[0]['result']['data']['json']['result']
        except (urllib.error.ContentTooShortError, urllib.error.HTTPError, urllib.error.URLError):
            raise Exception("문제의 실행 결과를 가져오지 못했습니다")

        if result['error']:
            raise Exception(f"{result['type']}\n{json.loads(result['message'])['stderr']}")

        return result

    def __write_result_block(self, result_file: TextIO, case: dict) -> None:
        result_file.write("--------------------\n\n")
        if 'reason' in case: # reason이 있으면 WA가 아닌 오답
            result_file.write(f"{self.RESULT_KOREAN[case['reason']]}\n\n")
            if case['stderr']:
                result_file.write(f"stderr:\n{case['stderr']}\n\n")
            result_file.write(f"입력:\n{case['testcase']}\n\n")
            result_file.write(f"정답 출력:\n{case['correctOutput']}\n")
        else:
            result_file.write(f"{self.RESULT_KOREAN['WA']}\n\n")
            result_file.write(f"입력:\n{case['testcase']}\n\n")
            result_file.write(f"오답 출력:\n{case['targetOutput']}\n\n")
            result_file.write(f"정답 출력:\n{case['correctOutput']}\n")
        result_file.write("--------------------\n\n")

    def test(self, problem_id: str, source_path: str) -> None:
        try:
            problem = self.__problem_fetcher(problem_id)
            with open(source_path, "r") as f:
                result = self.__stress_tester(problem_id, {
                    "targetCode": f.read(),
                    "problemExternalId": problem_id,
                    "targetCodeLang": "cpp",
                    "generatorCodeIds": [g['id'] for g in problem['generatorCodes']],
                    "correctCodeId": problem['correctCodes'][0]['id'],
                    "checkerCodeId": None,
                    "isPublic": True,
                    "useIndividualCases": True,
                })
        except Exception as e:
            print(e)
            return
        
        if result['totalCases'] == result['correctCasesCount']:
            print(f"\033[92m{self.RESULT_KOREAN['AC']}\033[0m")
            return

        print(f"총 테스트케이스 실행 개수: {result['totalCases']}")
        print(f"정답 개수: {result['correctCasesCount']}")
        print(f"반례 개수: {result['wrongCasesCount'] + result['executionFailedCasesCount']}")
        with open(self.RESULT_PATH, "w") as f:
            f.write(f"Boj {problem_id}\n")
            f.write(f"총 테스트케이스 실행 개수: {result['totalCases']}\n")
            f.write(f"정답 개수: {result['correctCasesCount']}\n")
            f.write(f"반례 개수: {result['wrongCasesCount'] + result['executionFailedCasesCount']}\n\n")
            for case in result['wrongCases'] + result['executionFailedCases']:
                self.__write_result_block(f, case)
        print(f"반례가 {self.RESULT_PATH}에 저장됐습니다")

def main() -> None:
    if len(argv) < 2:
        print("사용법: test.py <백준 문제번호> [소스코드 경로]")
        return

    tester = TestcaseAC()
    tester.test(argv[1], argv[2] if len(argv) > 2 else "./main.cpp")

if __name__ == "__main__":
    main()
