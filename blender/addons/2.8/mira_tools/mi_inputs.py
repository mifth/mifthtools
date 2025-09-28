
pass_keys = {'NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
             'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
             'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
             'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 'TRACKPADPAN', 'TRACKPADZOOM'}


def get_input_pass(pass_keys, key_inputs, event):
    if event.type in pass_keys:
        return True

    if key_inputs == 'Maya':
        if event.type in {'RIGHTMOUSE', 'LEFTMOUSE'} and event.alt and not event.shift and not event.ctrl:
            return True

    return False
