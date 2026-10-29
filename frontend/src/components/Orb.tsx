import { useEffect, useRef, useState } from 'react'

/** AI Referee orb: an original reactive Three.js sphere. Its motion + colour encode the judging state.
 *  Inspired by the interaction idea of Spline's "Reactive Orb" community file (no assets reused).
 *  Falls back to a CSS orb if WebGL is unavailable or the user prefers reduced motion. */
export type OrbState = 'idle' | 'watching' | 'processing' | 'verified' | 'review'

const TARGET: Record<OrbState, { amp: number; speed: number; color: [number, number, number]; glow: number }> = {
  idle: { amp: 0.1, speed: 0.35, color: [0.09, 0.49, 0.5], glow: 0.5 },
  watching: { amp: 0.17, speed: 0.7, color: [0.12, 0.62, 0.64], glow: 0.9 },
  processing: { amp: 0.3, speed: 1.9, color: [0.78, 0.64, 0.42], glow: 1.2 },
  verified: { amp: 0.05, speed: 0.3, color: [0.2, 0.72, 0.55], glow: 1.4 },
  review: { amp: 0.26, speed: 1.1, color: [0.73, 0.18, 0.22], glow: 1.1 },
}

export const ORB_LABEL: Record<OrbState, string> = {
  idle: 'Idle', watching: 'Watching play', processing: 'Processing evidence', verified: 'Evidence verified', review: 'Review required',
}

export function Orb({ state = 'idle', size = 360, className = '' }: { state?: OrbState; size?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const stateRef = useRef<OrbState>(state)
  const [fallback, setFallback] = useState(false)
  stateRef.current = state

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) { setFallback(true); return }
    let disposed = false
    let cleanup = () => {}
    ;(async () => {
      try {
        const THREE = await import('three')
        const el = ref.current
        if (!el || disposed) return
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        renderer.setSize(size, size)
        el.appendChild(renderer.domElement)
        const scene = new THREE.Scene()
        const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 10)
        camera.position.z = 3.2
        const uniforms = {
          uTime: { value: 0 }, uAmp: { value: 0.1 }, uSpeed: { value: 0.35 }, uGlow: { value: 0.5 },
          uColor: { value: new THREE.Color(0.09, 0.49, 0.5) }, uMouse: { value: new THREE.Vector2(0, 0) },
        }
        const mat = new THREE.ShaderMaterial({
          uniforms, transparent: true,
          vertexShader: `
            uniform float uTime, uAmp, uSpeed; uniform vec2 uMouse;
            varying vec3 vN; varying vec3 vP; varying float vD;
            float h(vec3 p){ return sin(p.x*3.1+uTime*uSpeed)*sin(p.y*2.7-uTime*uSpeed*1.2)*sin(p.z*3.3+uTime*uSpeed*.8); }
            void main(){
              vec3 p = position;
              float d = h(p*1.3) + .5*h(p*2.6+4.);
              float m = dot(normalize(p), normalize(vec3(uMouse, 1.0)));
              d += max(m,0.)*max(m,0.)*.35*length(uMouse);
              p += normal * d * uAmp; vD = d;
              vN = normalize(normalMatrix * normal); vP = (modelViewMatrix * vec4(p,1.)).xyz;
              gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.);
            }`,
          fragmentShader: `
            uniform vec3 uColor; uniform float uGlow; varying vec3 vN; varying vec3 vP; varying float vD;
            void main(){
              vec3 V = normalize(-vP);
              float fres = pow(1.0 - max(dot(normalize(vN), V), 0.), 2.4);
              vec3 base = mix(vec3(.07,.14,.23), uColor, .55 + .45*smoothstep(-.6,.8,vD));
              vec3 col = base + uColor * fres * uGlow + vec3(.8,.7,.5) * pow(max(dot(normalize(vN), normalize(vec3(.4,.7,.6))),0.), 24.) * .35;
              gl_FragColor = vec4(col, .96);
            }`,
        })
        const mesh = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 48), mat)
        scene.add(mesh)
        const ring = new THREE.Mesh(new THREE.TorusGeometry(1.45, 0.008, 8, 160), new THREE.MeshBasicMaterial({ color: 0xc6a36b, transparent: true, opacity: 0.55 }))
        ring.rotation.x = 1.15
        scene.add(ring)
        const onMove = (e: PointerEvent) => {
          const r = renderer.domElement.getBoundingClientRect()
          uniforms.uMouse.value.set(((e.clientX - r.left) / r.width - 0.5) * 2, -((e.clientY - r.top) / r.height - 0.5) * 2)
        }
        window.addEventListener('pointermove', onMove)
        let raf = 0
        const clock = new THREE.Clock()
        const tick = () => {
          const t = TARGET[stateRef.current]
          const k = 0.045
          uniforms.uTime.value += clock.getDelta()
          uniforms.uAmp.value += (t.amp - uniforms.uAmp.value) * k
          uniforms.uSpeed.value += (t.speed - uniforms.uSpeed.value) * k
          uniforms.uGlow.value += (t.glow - uniforms.uGlow.value) * k
          uniforms.uColor.value.r += (t.color[0] - uniforms.uColor.value.r) * k
          uniforms.uColor.value.g += (t.color[1] - uniforms.uColor.value.g) * k
          uniforms.uColor.value.b += (t.color[2] - uniforms.uColor.value.b) * k
          mesh.rotation.y += 0.0025 + uniforms.uSpeed.value * 0.002
          ring.rotation.z += 0.004 * (0.6 + uniforms.uSpeed.value)
          uniforms.uMouse.value.multiplyScalar(0.96)
          renderer.render(scene, camera)
          raf = requestAnimationFrame(tick)
        }
        tick()
        cleanup = () => {
          cancelAnimationFrame(raf)
          window.removeEventListener('pointermove', onMove)
          renderer.dispose(); mesh.geometry.dispose(); mat.dispose()
          renderer.domElement.remove()
        }
      } catch {
        setFallback(true)
      }
    })()
    return () => { disposed = true; cleanup() }
  }, [size])

  if (fallback) {
    const c = TARGET[state].color.map((v) => Math.round(v * 255)).join(',')
    return (
      <div className={className} style={{ width: size, height: size, display: 'grid', placeItems: 'center' }} role="img" aria-label={ORB_LABEL[state]}>
        <div style={{ width: size * 0.62, height: size * 0.62, borderRadius: '50%', background: `radial-gradient(circle at 35% 30%, rgb(${c}), #12243A 75%)`, boxShadow: `0 0 ${size * 0.15}px rgba(${c},.5)`, transition: 'all .6s' }} />
      </div>
    )
  }
  return <div ref={ref} className={className} style={{ width: size, height: size }} role="img" aria-label={`AI Referee: ${ORB_LABEL[state]}`} />
}
