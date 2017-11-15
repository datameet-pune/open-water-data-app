import { UPDATE_LAYERS } from '../actions/index';

export default function(state = {layers:{'rainfall': false, 'crop': false}, timeperiod: {}, selectedArea: {}}, action) {
  switch (action.type) {
    case UPDATE_LAYERS:
         state = {
            ...state,
            layers: {
    ...state.layers,
            rainfall: (action.payload.rainfall !== undefined) ? action.payload.rainfall : state.layers.rainfall
    }}
    state = {
        ...state,
        layers: {
    ...state.layers,
            crop: (action.payload.crop !== undefined) ? action.payload.crop : state.layers.crop
    }}

      return state;
  }
  return state;
}
