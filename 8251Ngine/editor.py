import sys
import os
import traceback

# 프로젝트 루트 경로를 시스템 경로에 추가 (모듈 import 오류 방지)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.core.app import App
from game.scenes.editor_scene import EditorScene

def print_controls():
    """에디터 조작법을 콘솔에 출력합니다."""
    print("\n" + "="*60)
    print("        🛠️  8251Ngine Map Editor - Control Guide  🛠️")
    print("="*60)
    print(" [ 🎮 Mode & File ]")
    print("   TAB        : 모드 변경 (FLOOR ➡ WALL ➡ OBJECT)")
    print("   S          : 맵 저장 (map_data.json)")
    print("   L          : 맵 불러오기 (map_data.json)")
    print("")
    print(" [ 🏗️ Editing ]")
    print("   L-Click    : 설치 (Place)")
    print("   R-Click    : 삭제 (Remove)")
    print("   [  /  ]    : 타일 모양 변경 (이전 / 다음)")
    print("   R          : 벽 회전 (WALL 모드에서만 동작)")
    print("")
    print(" [ 📷 Camera ]")
    print("   Arrow Keys : 카메라 이동")
    print("   Shift      : 빠르게 이동")
    print("="*60 + "\n")

def main():
    # 1. 에셋 디렉토리 확인 (없으면 생성)
    map_dir = "assets/maps"
    if not os.path.exists(map_dir):
        try:
            os.makedirs(map_dir)
            print(f"[System] '{map_dir}' 디렉토리가 생성되었습니다.")
        except OSError as e:
            print(f"[Warning] 디렉토리 생성 실패: {e}")

    # 2. 앱 초기화
    # 에디터는 네트워크 기능이 필요 없으므로 use_network=False로 설정
    print("[System] 엔진을 초기화하는 중...")
    app = App(
        width=1280, 
        height=720, 
        title="8251Ngine Map Editor (Zomboid Style)", 
        use_network=False
    )
    
    # 3. 에디터 씬 로드
    try:
        editor_scene = EditorScene()
        app.set_scene(editor_scene)
        print("[System] 에디터 씬이 성공적으로 로드되었습니다.")
    except Exception as e:
        print(f"[Error] 에디터 씬 로드 중 오류 발생: {e}")
        traceback.print_exc()
        return

    # 4. 조작법 출력
    print_controls()
    
    # 5. 메인 루프 실행
    print("[System] 에디터를 시작합니다...")
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[System] 사용자에 의해 에디터가 종료되었습니다.")
    except Exception as e:
        print(f"\n[Error] 실행 중 치명적인 오류 발생: {e}")
        traceback.print_exc()
    finally:
        print("[System] 8251Ngine Editor Closed.")

if __name__ == "__main__":
    main()