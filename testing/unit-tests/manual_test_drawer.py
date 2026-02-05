import flet as ft

def main(page: ft.Page):
    print("App started")
    
    def open_drawer(e):
        print("Button clicked")
        page.drawer.open = True
        page.drawer.update()
        print("Drawer update called")

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Text("Drawer Content"),
        ],
    )

    btn = ft.ElevatedButton("Open Drawer", on_click=open_drawer)
    page.add(btn)
    
    print("Attempting to open drawer programmatically...")
    try:
        page.drawer.open = True
        page.drawer.update()
        print("Success: page.drawer.open = True")
    except Exception as e:
        print(f"Failed: page.drawer.open = True. Error: {e}")
        
    try:
        page.open(page.drawer)
        print("Success: page.open(drawer)")
    except Exception as e:
        print(f"Failed: page.open(drawer). Error: {e}")

if __name__ == "__main__":
    print("Running app...")
    ft.app(target=main)
