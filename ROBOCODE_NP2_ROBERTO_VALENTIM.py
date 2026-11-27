import asyncio
import math
from robocode_tank_royale.bot_api import Bot, BotInfo, ScannedBotEvent # type: ignore


class PredictiveBot(Bot):
    def __init__(self, bot_info: BotInfo | None = None):
        super().__init__(bot_info)
        # Mantém arma e radar independentes do giro do tanque
        self.adjust_gun_for_body_turn = True
        self.adjust_radar_for_body_turn = True
        self.adjust_radar_for_gun_turn = True

    async def run(self) -> None:
        while self.running:
            # Gira o radar continuamente para localizar inimigos
            self.set_turn_radar_right(360)
            # Movimentação básica para não ficar parado
            self.set_forward(100)
            self.set_turn_right(45)
            await self.go()

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        # 1. Trava o radar no inimigo escaneado para manter dados atualizados
        radar_turn = self.calc_radar_bearing(e.x, e.y)
        self.set_turn_radar_right(radar_turn * 2)

        # 2. Define a potência do tiro e calcula a velocidade da bala (20 - 3 * potência)
        firepower = 2.0
        bullet_speed = self.calc_bullet_speed(firepower)

        # 3. Predição linear iterativa da posição futura do inimigo
        enemy_heading_rad = math.radians(e.direction)
        pred_x, pred_y = e.x, e.y

        for _ in range(15):
            distance = math.hypot(pred_x - self.x, pred_y - self.y)
            time_to_hit = distance / bullet_speed
            pred_x = e.x + math.cos(enemy_heading_rad) * e.speed * time_to_hit
            pred_y = e.y + math.sin(enemy_heading_rad) * e.speed * time_to_hit

            # Limita a predição às bordas da arena para evitar mirar fora do mapa
            margin = 18
            pred_x = max(margin, min(self.arena_width - margin, pred_x))
            pred_y = max(margin, min(self.arena_height - margin, pred_y))

        # 4. Gira o canhão para o ponto previsto e atira quando estiver alinhado
        gun_turn = self.calc_gun_bearing(pred_x, pred_y)
        self.set_turn_gun_right(gun_turn)

        if abs(gun_turn) < 5 and self.gun_heat == 0:
            self.set_fire(firepower)


if __name__ == "__main__":
    bot_info = BotInfo(
        name="PredictiveBot",
        version="1.0",
        authors=["SeuNome"],
        game_types=["classic", "melee", "1v1"],
    )
    bot = PredictiveBot(bot_info)
    asyncio.run(bot.start())
