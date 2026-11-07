import { useEffect, useState } from 'react'

// const [data, err] = useLoad(() => api.round(id), [id])
export function useLoad(fn, deps) {
  const [state, setState] = useState([null, null])
  useEffect(() => {
    let live = true
    fn().then((d) => live && setState([d, null]), (e) => live && setState([null, e]))
    return () => { live = false }
  }, deps)
  return state
}
