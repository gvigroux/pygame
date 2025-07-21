
import pygame
import cairo
import time

from game import Game


#sk_a4ea9842ff92c551a2190616767d8f558e3318d0c397324b

pygame.init()
game = Game(pygame)

# Load config
game.load()
game.load_objects()

# Cairo surface et contexte réutilisables
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *game.window_size)
ctx     = cairo.Context(surface)
screen  = pygame.display.set_mode((game.window_size[0], game.window_size[1]), pygame.DOUBLEBUF | pygame.SRCALPHA)
        



dt_history = []
clock = pygame.time.Clock()
last_time = time.perf_counter()
running = True
current_step = 0
obj_block = game.block_count(0)


while running:
    t0 = time.perf_counter()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False           
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  
                x, y = event.pos
                print(f"{x*100/game.window_size[0]:.1f}% / {y*100/game.window_size[1]:.1f}% at {game.age:.1f}s")
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                print("Ctrl+C détecté via clavier (pas SIGINT)")
                running = False

    current_time = time.perf_counter()
    dt = current_time - last_time
    last_time = current_time

    # ajustement du dt pour éviter les dépassements
    dt_history.append(dt)
    if len(dt_history) > 5:
        dt_history.pop(0)
    dt = sum(dt_history) / len(dt_history)

    # End of game
    if( game.is_finished(current_step) ):
        running = False


    #***********************************************************************
    # Destroyed objects

    game.clean()

    # Comptage des objets bloquants avant mise à jour
    prev_block_count = obj_block
    obj_block = game.block_count(current_step)

    # Avancement du step si plus de blocage
    if prev_block_count > 0 and obj_block == 0:
        current_step += 1

    #***********************************************************************
    # Check collisions 

    t1 = time.perf_counter()
    game.check_collisions()
   
    game.update(dt, current_step, clock, obj_block)

    
    t2 = time.perf_counter()

    #***********************************************************************
    # Cairo rendering

    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()

    
    t3 = time.perf_counter()

    #***********************************************************************
    # Draw

    #ga0me.draw_on_context(ctx, current_time)
    game.draw(screen, ctx, current_time)

    t4 = time.perf_counter()

    # Step 3 : Cairo to Pygame
    raw_buf = surface.get_data()
    img = pygame.image.frombuffer(raw_buf, game.window_size, "BGRA").convert_alpha()
 

    # Step 4 : Affichage
    screen.blit(img, (0, 0))

    #for object in game.objects:
    #    object.draw_surface(screen)


    pygame.display.flip()
    t5 = time.perf_counter()
    clock.tick(60)
 
    # Debug print
    #fps = clock.get_fps()
    #print(f"FIRST: {(t1 - t0)*1000:.2f} ms | UPDATE: {(t2 - t1)*1000:.2f} ms | BACK: {(t3 - t2)*1000:.2f} ms | DRAW {(t4 - t3)*1000:.2f} | BLIT {(t5 - t4)*1000:.2f} | TOTAL: {(t5 - t0)*1000:.2f} ms | dt={dt*1000:.2f}ms | FPS={fps:.2f}")
    #print(fps)
pygame.quit()



