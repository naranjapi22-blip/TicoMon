from poke_env.battle.pokemon import Pokemon
from poke_env.teambuilder import TeambuilderPokemon

tb = TeambuilderPokemon(
    species="raichualola",
    level=50
)

pokemon = Pokemon(
    gen=9,
    teambuilder=tb
)

print("Nombre:", pokemon.species)
print("Tipos:", pokemon.types)
print("Stats:", pokemon.stats)