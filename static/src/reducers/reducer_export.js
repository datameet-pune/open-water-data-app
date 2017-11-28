import { EXPORT_CROP } from '../actions/index';
import { EXPORT_RAINFALL } from '../actions/index';

export default function(
  state = {
    rainfall: { status: false, link: '' },
    crop: { status: false, link: '' }
  },
  action
) {
  switch (action.type) {
    case EXPORT_CROP:
      if (action.payload.data.status === 'success') {
        state = {
          ...state,
          crop: {
            ...state.crop,
            status: action.payload.data.status,
            link: action.payload.data.downloadUrl
          }
        };
        return state;
      }
    case EXPORT_RAINFALL:
      if (action.payload.data.status === 'success') {
        state = {
          ...state,
          crop: {
            ...state.crop,
            status: action.payload.data.status,
            link: action.payload.data.downloadUrl
          }
        };
        return state;
      }
  }
  return state;
}
