import { CHANGE_PAGE } from './types';

export default function changePage(payload) {
  return {
    type: CHANGE_PAGE,
    payload,
  };
}
