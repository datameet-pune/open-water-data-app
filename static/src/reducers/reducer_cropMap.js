import { UPDATE_CROP_MAP } from '../actions/index';

export default function(state = null, action) {
    switch (action.type) {
        case UPDATE_CROP_MAP:
            if (action.payload) {
                return action.payload.data;
            } else {
                return false;
            }

    }
    return state;
}
