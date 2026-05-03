export interface DangerZone {
  lat: number
  lng: number
  radius: number // metres
  label: string
}

export interface CoastlinePoint {
  lat: number
  lng: number
}

export interface Spot {
  id: string
  name: string
  region: 'north' | 'east' | 'south' | 'west'
  lat: number
  lng: number
  refLat: number
  refLng: number
  pointId: string
  dangerZones: DangerZone[]
  coastline: CoastlinePoint[]
  bounds: [number, number, number, number]
}

export const SPOTS: Spot[] = [
  {
    id: 'wushih-north',
    name: '烏石港北堤',
    region: 'east',
    lat: 24.873217,
    lng: 121.843443,
    refLat: 24.873217,
    refLng: 121.843443,
    pointId: '6502600C01',
    dangerZones: [
      { lat: 24.8745, lng: 121.8415, radius: 50, label: '北堤防波堤' },
    ],
    coastline: [
      { lat: 24.877, lng: 121.840 },
      { lat: 24.875, lng: 121.842 },
      { lat: 24.873, lng: 121.843 },
      { lat: 24.871, lng: 121.844 },
      { lat: 24.869, lng: 121.844 },
    ],
    bounds: [24.867, 121.838, 24.879, 121.852],
  },
  {
    id: 'wushih-long',
    name: '烏石港長堤',
    region: 'east',
    lat: 24.869675,
    lng: 121.842931,
    refLat: 24.869675,
    refLng: 121.842931,
    pointId: '6502600C01',
    dangerZones: [
      { lat: 24.8685, lng: 121.841, radius: 50, label: '長堤礁石' },
    ],
    coastline: [
      { lat: 24.873, lng: 121.840 },
      { lat: 24.871, lng: 121.842 },
      { lat: 24.870, lng: 121.843 },
      { lat: 24.868, lng: 121.844 },
      { lat: 24.866, lng: 121.844 },
    ],
    bounds: [24.863, 121.837, 24.877, 121.851],
  },
  {
    id: 'shuangshi',
    name: '雙獅',
    region: 'east',
    lat: 24.889075,
    lng: 121.851077,
    refLat: 24.889075,
    refLng: 121.851077,
    pointId: '6502600C01',
    dangerZones: [
      { lat: 24.888, lng: 121.849, radius: 60, label: '礁石群' },
    ],
    coastline: [
      { lat: 24.893, lng: 121.848 },
      { lat: 24.891, lng: 121.850 },
      { lat: 24.889, lng: 121.851 },
      { lat: 24.887, lng: 121.852 },
      { lat: 24.885, lng: 121.852 },
    ],
    bounds: [24.883, 121.846, 24.897, 121.860],
  },
  {
    id: 'honeymoon',
    name: '蜜月灣',
    region: 'east',
    lat: 24.932403,
    lng: 121.886903,
    refLat: 24.932403,
    refLng: 121.886903,
    pointId: '6502600C02',
    dangerZones: [
      { lat: 24.934, lng: 121.885, radius: 40, label: '北側礁石' },
      { lat: 24.930, lng: 121.885, radius: 40, label: '南側礁石' },
    ],
    coastline: [
      { lat: 24.936, lng: 121.883 },
      { lat: 24.934, lng: 121.885 },
      { lat: 24.932, lng: 121.887 },
      { lat: 24.930, lng: 121.888 },
      { lat: 24.928, lng: 121.887 },
    ],
    bounds: [24.926, 121.881, 24.940, 121.895],
  },
  {
    id: 'jialeshuei',
    name: '佳樂水',
    region: 'south',
    lat: 21.987589,
    lng: 120.846707,
    refLat: 21.987589,
    refLng: 120.846707,
    pointId: '6500900C01',
    dangerZones: [
      { lat: 21.988, lng: 120.845, radius: 50, label: '礁岩區' },
    ],
    coastline: [
      { lat: 21.991, lng: 120.844 },
      { lat: 21.989, lng: 120.846 },
      { lat: 21.988, lng: 120.847 },
      { lat: 21.986, lng: 120.848 },
      { lat: 21.984, lng: 120.848 },
    ],
    bounds: [21.981, 120.841, 21.995, 120.855],
  },
  {
    id: 'wuwei',
    name: '無尾港',
    region: 'east',
    lat: 24.612491,
    lng: 121.864590,
    refLat: 24.612491,
    refLng: 121.864590,
    pointId: '6502600C03',
    dangerZones: [
      { lat: 24.614, lng: 121.863, radius: 50, label: '港口防波堤' },
    ],
    coastline: [
      { lat: 24.616, lng: 121.861 },
      { lat: 24.614, lng: 121.863 },
      { lat: 24.612, lng: 121.865 },
      { lat: 24.610, lng: 121.866 },
      { lat: 24.608, lng: 121.866 },
    ],
    bounds: [24.606, 121.858, 24.620, 121.872],
  },
]

export const SPOTS_BY_ID = Object.fromEntries(SPOTS.map(s => [s.id, s]))
