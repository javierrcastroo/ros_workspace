# vc_battleship

Guía breve para poner en marcha el puente entre el tablero y el UR3.

## Prerrequisitos
- Workspace compilado con `catkin_make` y entorno cargado: `source devel/setup.bash`.
- Driver del UR y MoveIt activos (por ejemplo, `launcher_robots_lab_robotica/launch/robot_203.launch` o el que corresponda a tu robot/simulación).
- Nodo que publique el layout del tablero como `geometry_msgs/PoseArray` en `/board/cell_centers` y mensajes `std_msgs/String` con la celda a atacar en `/attack_cell`.

## Lanzar la tubería de ataque
1. Arranca el driver del robot y MoveIt con el launch adecuado a tu robot (p. ej. `roslaunch launcher_robots_lab_robotica robot_203.launch`). Esto arranca controladores, `robot_state_publisher` y MoveIt.
2. En otra consola (con el entorno devel cargado), lanza la tubería del tablero:
   ```bash
   roslaunch vc_battleship board_attack_pipeline.launch \
     rows:=10 cols:=10 row_labels:=A,B,C,D,E,F,G,H,I,J \
     approach_offset:=0.10 move_group:=manipulator
   ```
   - `rows`, `cols`, `row_labels`: definen el grid del tablero y las etiquetas de fila que recibirá el nodo `board_cell_mapper.py`.
   - `approach_offset`: altura extra en metros para la pose de aproximación antes de bajar a la casilla (usada por `attack_motion_executor.py`).
   - `move_group`: nombre del grupo MoveIt que controla el UR3.

## Flujo de datos
- `/board/cell_centers` (`PoseArray`): layout del tablero; cada entrada representa el centro de una casilla en el `frame_id` del tablero. Debe contener `rows * cols` poses.
- `/attack_cell` (`String`): etiqueta de casilla objetivo (ej. `B7`).
- `/board/attack_target_pose` (`PoseStamped`): pose resultante publicada por `board_cell_mapper.py`.
- `/robot/attack_status` (`String`): estado del movimiento publicado por `attack_motion_executor.py` (`succeeded`, `failed_approach`, `failed_target`).

## Probar rápidamente
- Publica un layout de prueba (10x10) usando `rostopic pub /board/cell_centers geometry_msgs/PoseArray ...` o tu nodo de cámara/visión.
- Envía un ataque de ejemplo: `rostopic pub /attack_cell std_msgs/String "data: 'B7'" -1`.
- Revisa el resultado en `/robot/attack_status` y los logs en terminal.

## Notas
- `attack_motion_executor.py` fija la orientación de la herramienta con `orientation_rpy` (por defecto `[pi, 0, 0]`, herramienta apuntando hacia abajo). Ajusta este parámetro si tu herramienta requiere otra orientación.
- Si no llega ningún layout, `board_cell_mapper.py` ignora las órdenes de ataque hasta recibir un `PoseArray` con el número de celdas esperado.
