from Task import Task
import bitmap as bm
import config


class ExTask(Task):
    def __init__(self, bitmaps):
        Task.__init__(self, bitmaps)
        self.target_state_idx = -1

    def get_first_guidance(self):
        result = {'status': 'success'}

        self.target_state_idx = 0
        target_state = self.get_state(self.target_state)

        result['speech'] = \
            "Welcome to the Lego task. As a first step, please " \
            "find a piece of 1x%d %s brick and put it on the " \
            "board." % (self.target_state.shape[1],
                        config.COLOR_ORDER[target_state[0, 0]])
        result['animation'] = bm.bitmap2guidance_animation(target_state,
                                                           config.ACTION_TARGET)
        result['time_estimate'] = self.time_estimates[0]
        img_guidance = bm.bitmap2guidance_img(target_state, None,
                                              config.ACTION_TARGET)
        return result, img_guidance

    def search_next(self, current_state, bm_diffs, search_type='more'):
        pass  # todo

    def get_guidance(self):
        result = {'status': 'success'}
        target_state = self.get_state(self.target_state_idx)

        ## Check if we at least reached the previously desired state
        if bm.bitmap_same(self.current_state, target_state):
            ## Task is done
            if self.is_final_state():
                result['speech'] = "You have completed the task. " \
                                   "Congratulations!"
                result['animation'] = bm.bitmap2guidance_animation(
                    self.current_state, config.ACTION_TARGET)
                img_guidance = bm.bitmap2guidance_img(self.current_state, None,
                                                      config.ACTION_TARGET)
                return result, img_guidance

            ## Not done
            ## Next state is simply the next one in line
            self.target_state_idx += 1

            ## Determine the type of change needed for the next step

        else:
            result['speech'] = "This is incorrect, please undo the last " \
                               "step and revert to the model shown on " \
                               "the screen."
            result['animation'] = bm.bitmap2guidance_animation(
                self.prev_good_state, config.ACTION_TARGET)
            img_guidance = bm.bitmap2guidance_img(self.prev_good_state, None,
                                                  config.ACTION_TARGET)
            return result, img_guidance
