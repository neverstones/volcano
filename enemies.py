import pygame, math

class Enemy:
	def __init__(self, x, y, enemy_type='lava_blob'):
		self.x = x
		self.y = y
		self.start_x = x
		self.type = enemy_type
		self.health = 1
		self.radius = 15
		self.vx = 0
		self.vy = 0
		self.animation_time = 0
		self.patrol_distance = 100
		self.direction = 1

		# Tipi di nemici vulcanologici
		if enemy_type == 'lava_blob':
			self.color = (255, 69, 0)
			self.speed = 1
			self.damage = 1
		elif enemy_type == 'gas_cloud':
			self.color = (128, 128, 128)
			self.speed = 0.5
			self.damage = 1
			self.radius = 25
		elif enemy_type == 'rock_fragment':
			self.color = (139, 69, 19)
			self.speed = 2
			self.damage = 2
		elif enemy_type == 'pyroclastic_flow':
			self.color = (64, 64, 64)
			self.speed = 3
			self.damage = 3
			self.radius = 30

	def update(self, dt, world_offset):
		self.animation_time += dt * 2

		if self.type == 'lava_blob':
			# Movimento di pattugliamento
			self.x += self.direction * self.speed
			if abs(self.x - self.start_x) > self.patrol_distance:
				self.direction *= -1

		elif self.type == 'gas_cloud':
			# Movimento fluttuante
			self.x += math.sin(self.animation_time) * 0.5
			self.y += math.cos(self.animation_time * 0.7) * 0.3

		elif self.type == 'rock_fragment':
			# Movimento erratico - VERSIONE STABILE
			time_check = int(pygame.time.get_ticks() / 100) % 100
			fragment_id = int(self.x + self.y) % 100
			if (time_check + fragment_id) % 100 < 10:
				seed = (time_check + fragment_id) % 1000
				self.vx = ((seed % 400) - 200) / 100.0
				self.vy = ((seed % 200) - 100) / 100.0
			self.x += self.vx * dt
			self.y += self.vy * dt

		elif self.type == 'pyroclastic_flow':
			# Movimento verso il basso
			self.y += self.speed

	def draw(self, surface, world_offset):
		screen_y = self.y + world_offset
		HEIGHT = 800 # Assicurati che sia coerente con il resto del progetto
		if -50 < screen_y < HEIGHT + 50:
			if self.type == 'lava_blob':
				pulse = 0.8 + 0.2 * math.sin(self.animation_time * 3)
				radius = int(self.radius * pulse)
				glow_surface = pygame.Surface((radius*3, radius*3), pygame.SRCALPHA)
				pygame.draw.circle(glow_surface, (255, 100, 0, 100), (int(radius*1.5), int(radius*1.5)), int(radius*1.5))
				surface.blit(glow_surface, (self.x - radius*1.5, screen_y - radius*1.5))
				pygame.draw.circle(surface, self.color, (int(self.x), int(screen_y)), radius)
				pygame.draw.circle(surface, (255, 200, 0), (int(self.x), int(screen_y)), radius//2)
			elif self.type == 'gas_cloud':
				cloud_seed = int(self.x + self.y) % 1000
				time_seed = int(pygame.time.get_ticks() / 500) % 100
				for i in range(5):
					particle_seed = (cloud_seed + time_seed + i * 13) % 1000
					offset_x = ((particle_seed % 21) - 10)
					offset_y = (((particle_seed + 21) % 21) - 10)
					size = self.radius//2 + ((particle_seed % (self.radius//2 + 1)))
					alpha = 50 + (particle_seed % 51)
					cloud_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
					pygame.draw.circle(cloud_surface, (*self.color, alpha), (size, size), size)
					surface.blit(cloud_surface, (self.x + offset_x - size, screen_y + offset_y - size))
			elif self.type == 'rock_fragment':
				fragment_seed = int(self.x + self.y) % 1000
				points = []
				for i in range(6):
					angle = i * math.pi / 3 + self.animation_time
					variance = 0.8 + ((fragment_seed + i * 7) % 40) / 100.0
					x = self.x + self.radius * variance * math.cos(angle)
					y = screen_y + self.radius * variance * math.sin(angle)
					points.append((x, y))
				pygame.draw.polygon(surface, self.color, points)
				pygame.draw.polygon(surface, (200, 200, 200), points, 2)
			elif self.type == 'pyroclastic_flow':
				flow_seed = int(self.x + self.y) % 1000
				time_seed = int(pygame.time.get_ticks() / 300) % 100
				for i in range(10):
					particle_seed = (flow_seed + time_seed + i * 11) % 1000
					x_offset = ((particle_seed % (self.radius * 2 + 1)) - self.radius)
					y_offset = (((particle_seed + 100) % (self.radius + 1)) - self.radius//2)
					size = 5 + (particle_seed % (self.radius//2 - 4))
					alpha = 100 + (particle_seed % 101)
					flow_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
					pygame.draw.circle(flow_surface, (*self.color, alpha), (size, size), size)
					surface.blit(flow_surface, (self.x + x_offset - size, screen_y + y_offset - size))

	def check_collision(self, player):
		distance = math.hypot(player.x - self.x, player.y - self.y)
		return distance < (self.radius + player.radius)
